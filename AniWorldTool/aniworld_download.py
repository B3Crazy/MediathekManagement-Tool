#!/usr/bin/env python3
"""Simple non-interactive AniLoad wrapper."""

from __future__ import annotations

import argparse
import contextlib
import html
import importlib
import logging
import os
import queue
import re
import subprocess
import sys
import threading
from collections.abc import Callable
from pathlib import Path

RICH_AVAILABLE = None


DEFAULT_ACTIONS = ("download", "watch", "syncplay")
PREFERRED_PROVIDERS = ("Filemoon", "Vidmoly", "VOE")


def _load_aniworld_api():
	try:
		config = importlib.import_module("aniworld.config")
		providers = importlib.import_module("aniworld.providers")
	except ModuleNotFoundError as exc:
		raise ModuleNotFoundError(
			"The aniworld package is not installed in the active Python environment."
		) from exc

	def _run_action(obj, action: str):
		if action not in config.ACTION_METHODS.values():
			raise ValueError(f"Invalid action: {action}")
		getattr(obj, action)()

	return config.ACTION_METHODS, providers.resolve_provider, _run_action


def _load_search_api() -> Callable[[str], list[dict]]:
	try:
		config = importlib.import_module("aniworld.config")
	except ModuleNotFoundError as exc:
		raise ModuleNotFoundError(
			"The aniworld package is not installed in the active Python environment."
		) from exc

	search_url = "https://aniworld.to/ajax/search"

	def _query(keyword: str) -> list[dict]:
		response = config.GLOBAL_SESSION.post(search_url, data={"keyword": keyword})
		try:
			data = response.json()
		except ValueError:
			return []
		return data if isinstance(data, list) else []

	return _query


def _load_menu_language_extractor() -> Callable[[str, dict], list[str]]:
	try:
		menu_module = importlib.import_module("aniworld.menu")
		return menu_module._extract_menu_languages
	except ModuleNotFoundError as exc:
		if exc.name not in {"_curses", "curses"}:
			raise ModuleNotFoundError(
				"The aniworld package is not installed in the active Python environment."
			) from exc

	try:
		config = importlib.import_module("aniworld.config")
	except ModuleNotFoundError as exc:
		raise ModuleNotFoundError(
			"The aniworld package is not installed in the active Python environment."
		) from exc

	def _extract_menu_languages(provider_name: str, provider_data: dict) -> list[str]:
		languages: list[str] = []

		if provider_name == "AniWorld":
			for key in provider_data.keys():
				site_key = config.INVERSE_LANG_KEY_MAP.get(key)
				if site_key is None:
					continue
				label = config.LANG_LABELS.get(site_key)
				if label and label not in languages:
					languages.append(label)
			return languages

		if provider_name == "SerienStream":
			for key in provider_data.keys():
				if not (isinstance(key, tuple) and len(key) == 2):
					continue
				audio = getattr(key[0], "value", str(key[0]))
				audio_lower = str(audio).lower()
				if audio_lower == "german":
					label = "German Dub"
				elif audio_lower == "english":
					label = "English Dub"
				else:
					continue
				if label not in languages:
					languages.append(label)

		return languages

	return _extract_menu_languages


def _load_menu_provider_extractor() -> Callable[[dict], list[str]]:
	try:
		menu_module = importlib.import_module("aniworld.menu")
		return menu_module._extract_menu_providers
	except ModuleNotFoundError as exc:
		if exc.name not in {"_curses", "curses"}:
			raise ModuleNotFoundError(
				"The aniworld package is not installed in the active Python environment."
			) from exc

	def _extract_menu_providers(provider_data: dict) -> list[str]:
		provider_names: set[str] = set()
		for providers_map in provider_data.values():
			if isinstance(providers_map, dict):
				provider_names.update(str(p) for p in providers_map.keys())
		return sorted(provider_names)

	return _extract_menu_providers


def _suppress_aniworld_warning_logs():
	for name in list(logging.Logger.manager.loggerDict):
		if name.startswith("aniworld"):
			logging.getLogger(name).setLevel(logging.ERROR)


def _is_ffmpeg_like_command(cmd) -> bool:
	if not cmd:
		return False

	if isinstance(cmd, (list, tuple)):
		if not cmd:
			return False
		binary = str(cmd[0])
	else:
		parts = str(cmd).strip().split()
		if not parts:
			return False
		binary = parts[0]

	binary_name = os.path.basename(binary).lower()
	return binary_name in {"ffmpeg", "ffmpeg.exe", "ffprobe", "ffprobe.exe"}


@contextlib.contextmanager
def _suppress_ffmpeg_output():
	original_popen = subprocess.Popen

	def _quiet_popen(*args, **kwargs):
		command = kwargs.get("args")
		if command is None and args:
			command = args[0]

		if _is_ffmpeg_like_command(command):
			kwargs.setdefault("stdout", subprocess.DEVNULL)
			kwargs.setdefault("stderr", subprocess.DEVNULL)

		return original_popen(*args, **kwargs)

	subprocess.Popen = _quiet_popen
	try:
		yield
	finally:
		subprocess.Popen = original_popen


@contextlib.contextmanager
def _suppress_ffmpeg_python_output():
	try:
		import ffmpeg
	except Exception:
		yield
		return

	original_module_run = getattr(ffmpeg, "run", None)
	original_output_run = getattr(ffmpeg.nodes.OutputStream, "run", None)

	def _quiet_module_run(stream_spec, *args, **kwargs):
		kwargs.setdefault("quiet", True)
		if not callable(original_module_run):
			return None
		return original_module_run(stream_spec, *args, **kwargs)

	def _quiet_output_run(self, *args, **kwargs):
		kwargs.setdefault("quiet", True)
		if not callable(original_output_run):
			return None
		return original_output_run(self, *args, **kwargs)

	if callable(original_module_run):
		ffmpeg.run = _quiet_module_run
	if callable(original_output_run):
		setattr(ffmpeg.nodes.OutputStream, "run", _quiet_output_run)

	try:
		yield
	finally:
		if callable(original_module_run):
			ffmpeg.run = original_module_run
		if callable(original_output_run):
			setattr(ffmpeg.nodes.OutputStream, "run", original_output_run)


@contextlib.contextmanager
def _suppress_download_noise():
	with _suppress_ffmpeg_output(), _suppress_ffmpeg_python_output():
		yield


def _provider_candidates_for_language(provider, episode_url: str, language: str) -> list[str]:
	probe = provider.episode_cls(url=episode_url, selected_language=language)
	provider_data = probe.provider_data
	provider_dict = provider_data._data if hasattr(provider_data, "_data") else provider_data

	candidates: list[str] = []
	for p in PREFERRED_PROVIDERS:
		try:
			if probe.provider_link(language, p):
				candidates.append(p)
		except Exception:
			pass

	for providers_map in provider_dict.values():
		if not isinstance(providers_map, dict):
			continue
		for p in providers_map.keys():
			if p not in candidates:
				candidates.append(p)

	return candidates or ["VOE"]


def _load_rich_components():
	global RICH_AVAILABLE
	if RICH_AVAILABLE is False:
		return None

	try:
		rich_console = importlib.import_module("rich.console")
		rich_panel = importlib.import_module("rich.panel")
		rich_progress = importlib.import_module("rich.progress")
		RICH_AVAILABLE = True
		return {
			"Console": rich_console.Console,
			"Panel": rich_panel.Panel,
			"Table": importlib.import_module("rich.table").Table,
			"Prompt": importlib.import_module("rich.prompt").Prompt,
			"IntPrompt": importlib.import_module("rich.prompt").IntPrompt,
			"Confirm": importlib.import_module("rich.prompt").Confirm,
			"Progress": rich_progress.Progress,
			"SpinnerColumn": rich_progress.SpinnerColumn,
			"TextColumn": rich_progress.TextColumn,
			"BarColumn": rich_progress.BarColumn,
			"TaskProgressColumn": rich_progress.TaskProgressColumn,
			"TimeElapsedColumn": rich_progress.TimeElapsedColumn,
			"Markdown": importlib.import_module("rich.markdown").Markdown,
		}
	except Exception:
		RICH_AVAILABLE = False
		return None


def _build_parser() -> argparse.ArgumentParser:
	try:
		action_methods, _, _ = _load_aniworld_api()
		action_choices = sorted(action_methods.values())
	except Exception:
		# Keep CLI usable for --help even if aniworld is not available.
		action_choices = list(DEFAULT_ACTIONS)

	parser = argparse.ArgumentParser(
		description="Download/watch AniWorld episodes from URLs using the aniworld package."
	)
	parser.add_argument(
		"urls",
		nargs="*",
		help="Episode, season, or series URLs.",
	)
	parser.add_argument(
		"-f",
		"--url-file",
		type=Path,
		help="Text file with one URL per line.",
	)
	parser.add_argument(
		"-a",
		"--action",
		choices=action_choices,
		default="download",
		help="Action to run for each URL.",
	)
	parser.add_argument(
		"-s",
		"--search",
		help="Search AniWorld by series name and choose from matching results.",
	)
	parser.add_argument(
		"--no-interactive",
		action="store_true",
		help="Disable interactive menu when using --search and auto-pick the first result.",
	)
	parser.add_argument(
		"--all-languages",
		action="store_true",
		help="For downloads, fetch all available dubs/subs and merge them into one MKV.",
	)
	parser.add_argument(
		"--no-visual",
		action="store_true",
		help="Disable the visual console frontend for downloads.",
	)
	return parser


def _print_startup_banner() -> None:
	banner = r"""

█████████               ███  █████                              █████
  ███░░░░░███             ░░░  ░░███                              ░░███
 ░███    ░███  ████████   ████  ░███         ██████   ██████    ███████
 ░███████████ ░░███░░███ ░░███  ░███        ███░░███ ░░░░░███  ███░░███
 ░███░░░░░███  ░███ ░███  ░███  ░███       ░███ ░███  ███████ ░███ ░███
 ░███    ░███  ░███ ░███  ░███  ░███      █░███ ░███ ███░░███ ░███ ░███
 █████   █████ ████ █████ █████ ███████████░░██████ ░░████████░░████████
░░░░░   ░░░░░ ░░░░ ░░░░░ ░░░░░ ░░░░░░░░░░░  ░░░░░░   ░░░░░░░░  ░░░░░░░░

"""
	print(banner)


def _read_url_file(file_path: Path | None) -> list[str]:
	if file_path is None:
		return []
	if not file_path.exists():
		raise FileNotFoundError(f"URL file not found: {file_path}")
	return [
		line.strip()
		for line in file_path.read_text(encoding="utf-8").splitlines()
		if line.strip() and not line.strip().startswith("#")
	]


def _build_object(url: str, resolve_provider):
	provider = resolve_provider(url)

	if provider.episode_pattern and provider.episode_pattern.fullmatch(url):
		return provider.episode_cls(url=url)
	if provider.season_pattern and provider.season_pattern.fullmatch(url):
		return provider.season_cls(url=url)
	if provider.series_pattern and provider.series_pattern.fullmatch(url):
		return provider.series_cls(url=url)

	raise ValueError(f"Unsupported URL format for provider {provider.name}: {url}")


def _normalize_search_results(raw_results) -> list[dict[str, str]]:
	if not raw_results:
		return []

	results = raw_results if isinstance(raw_results, list) else [raw_results]
	normalized: list[dict[str, str]] = []

	for item in results:
		link = str(item.get("link", "")).strip()
		if not link.startswith("/anime/stream/"):
			continue

		title = _clean_text(str(item.get("title") or item.get("name") or "Unknown Title"))
		normalized.append(
			{
				"title": title,
				"url": f"https://aniworld.to{link}",
			}
		)

	return normalized


def _clean_text(value: str | None) -> str:
	if value is None:
		return ""
	text = html.unescape(str(value))
	text = re.sub(r"<[^>]+>", "", text)
	text = re.sub(r"\s+", " ", text)
	return text.strip()


def _pick_result_with_frontend(results: list[dict[str, str]], non_interactive: bool) -> str:
	if not results:
		raise ValueError("No matching stream results found for the given search.")

	if non_interactive or len(results) == 1:
		choice = results[0]
		print(f"Selected: {choice['title']} -> {choice['url']}")
		return choice["url"]

	print("\nSearch results:")
	for index, result in enumerate(results, start=1):
		print(f"{index:>2}. {result['title']}")

	while True:
		picked = input("\nChoose a series number (q to quit): ").strip().lower()
		if picked in {"q", "quit", "exit"}:
			raise KeyboardInterrupt("Selection canceled by user.")
		if not picked.isdigit():
			print("Please enter a valid number.")
			continue

		selection = int(picked)
		if 1 <= selection <= len(results):
			chosen = results[selection - 1]
			print(f"Selected: {chosen['title']} -> {chosen['url']}")
			return chosen["url"]

		print(f"Number out of range. Pick 1-{len(results)}.")


def _search_url_from_name(name: str, non_interactive: bool) -> str:
	query = _load_search_api()
	raw_results = query(name)
	results = _normalize_search_results(raw_results)
	return _pick_result_with_frontend(results, non_interactive)


def _parse_episode_selection(raw: str, max_episode: int) -> list[int]:
	raw = raw.strip().lower()
	if raw in {"all", "a", "*"}:
		return list(range(1, max_episode + 1))

	selected: set[int] = set()
	for part in raw.split(","):
		part = part.strip()
		if not part:
			continue
		if "-" in part:
			start_s, end_s = part.split("-", 1)
			start = int(start_s)
			end = int(end_s)
			for idx in range(min(start, end), max(start, end) + 1):
				if 1 <= idx <= max_episode:
					selected.add(idx)
		else:
			idx = int(part)
			if 1 <= idx <= max_episode:
				selected.add(idx)

	if not selected:
		raise ValueError("No valid episode selection provided.")

	return sorted(selected)


def _interactive_frontend_wizard(resolve_provider, initial_search: str | None = None) -> dict:
	rich_components = _load_rich_components()
	extract_menu_languages = _load_menu_language_extractor()
	extract_menu_providers = _load_menu_provider_extractor()

	if rich_components:
		console = rich_components["Console"]()
	else:
		console = None

	query = _load_search_api()

	while True:
		keyword = (initial_search or "").strip()
		if not keyword:
			keyword = input("Search anime name: ").strip()
		if not keyword:
			raise ValueError("Search term cannot be empty.")

		results = _normalize_search_results(query(keyword))
		if not results:
			print("No search results found. Try another name.")
			initial_search = None
			continue

		if console is not None and rich_components:
			table = rich_components["Table"](title="Search Results")
			table.add_column("#", style="cyan", justify="right")
			table.add_column("Title", style="bold")
			for i, item in enumerate(results, start=1):
				table.add_row(str(i), item["title"])
			console.print(table)
			series_idx = rich_components["IntPrompt"].ask(
				"Pick series number",
				default=1,
				choices=[str(i) for i in range(1, len(results) + 1)],
			)
		else:
			print("\nSearch Results:")
			for i, item in enumerate(results, start=1):
				print(f"{i:>2}. {item['title']}")
			series_idx = int(input("Pick series number: ").strip())

		selected_series = results[series_idx - 1]
		series_url = selected_series["url"]
		provider = resolve_provider(series_url)
		series_obj = provider.series_cls(url=series_url)
		break

	series_title = getattr(series_obj, "title", selected_series["title"]) or selected_series["title"]
	series_title = _clean_text(series_title)
	release_year = getattr(series_obj, "release_year", "?")
	rating = getattr(series_obj, "rating", "?")
	genres = ", ".join(_clean_text(g) for g in (getattr(series_obj, "genres", None) or []))
	country = _clean_text(getattr(series_obj, "country", "") or "")
	description = _clean_text(getattr(series_obj, "description", "") or "")

	if console is not None and rich_components:
		console.print(
			rich_components["Panel"](
				f"[bold cyan]{series_title}[/bold cyan]\n"
				f"[bold]Year:[/bold] {release_year}    [bold]Rating:[/bold] {rating}\n"
				f"[bold]Country:[/bold] {country or '-'}\n"
				f"[bold]Genres:[/bold] {genres or '-'}",
				title="Selected Anime",
				border_style="bright_magenta",
			)
		)
		if description:
			console.print(
				rich_components["Panel"](
					rich_components["Markdown"](description[:700]),
					title="Description",
					border_style="blue",
				)
			)

	seasons = list(series_obj.seasons)
	if not seasons:
		raise ValueError("No seasons found for selected series.")

	if console is not None and rich_components:
		table = rich_components["Table"](title="Seasons")
		table.add_column("#", justify="right", style="cyan")
		table.add_column("Season")
		table.add_column("Episodes", justify="right")
		for i, season in enumerate(seasons, start=1):
			table.add_row(str(i), str(season.season_number), str(season.episode_count))
		console.print(table)

	if console is not None and rich_components:
		all_seasons = rich_components["Confirm"].ask("Select all seasons?", default=True)
	else:
		all_seasons = input("Select all seasons? [Y/n]: ").strip().lower() in {"", "y", "yes"}

	if all_seasons:
		chosen_seasons = seasons
	else:
		if console is not None and rich_components:
			season_input = rich_components["Prompt"].ask("Choose season numbers (e.g. 1,3 or 2-4)")
		else:
			season_input = input("Choose season numbers (e.g. 1,3 or 2-4): ")
		season_indexes = _parse_episode_selection(season_input, len(seasons))
		chosen_seasons = [seasons[i - 1] for i in season_indexes]

	episode_urls: list[str] = []
	for season in chosen_seasons:
		episodes = list(season.episodes)
		if not episodes:
			continue

		if console is not None and rich_components:
			table = rich_components["Table"](title=f"Season {season.season_number} Episodes")
			table.add_column("#", justify="right", style="cyan")
			table.add_column("Episode", justify="right")
			table.add_column("Title", style="bold")
			table.add_column("Languages", style="green")
			table.add_column("Providers", style="yellow")
			for i, ep in enumerate(episodes, start=1):
				provider_data = ep.provider_data
				provider_dict = provider_data._data if hasattr(provider_data, "_data") else provider_data
				langs = extract_menu_languages(resolve_provider(ep.url).name, provider_dict)
				providers = extract_menu_providers(provider_dict)
				table.add_row(
					str(i),
					str(getattr(ep, "episode_number", i)),
					_clean_text(getattr(ep, "title", "") or "-"),
					", ".join(langs) if langs else "-",
					", ".join(providers) if providers else "-",
				)
			console.print(table)
			all_eps = rich_components["Confirm"].ask(
				f"Select all episodes from season {season.season_number}?",
				default=True,
			)
		else:
			all_eps = input(f"Select all episodes from season {season.season_number}? [Y/n]: ").strip().lower() in {"", "y", "yes"}

		if all_eps:
			episode_urls.extend(ep.url for ep in episodes)
			continue

		if console is not None and rich_components:
			episode_input = rich_components["Prompt"].ask(
				f"Choose episodes for season {season.season_number} (e.g. 1,3 or 2-5)"
			)
		else:
			episode_input = input(
				f"Choose episodes for season {season.season_number} (e.g. 1,3 or 2-5): "
			)

		episode_indexes = _parse_episode_selection(episode_input, len(episodes))
		episode_urls.extend(episodes[i - 1].url for i in episode_indexes)

	if not episode_urls:
		raise ValueError("No episodes selected.")

	if console is not None and rich_components:
		action = rich_components["Prompt"].ask("Action", choices=list(DEFAULT_ACTIONS), default="download")
	else:
		action = input("Action (download/watch/syncplay) [download]: ").strip().lower() or "download"
		if action not in DEFAULT_ACTIONS:
			action = "download"

	if action == "download":
		if console is not None and rich_components:
			all_languages = rich_components["Confirm"].ask("Download all dubs/subs into same MKV?", default=True)
			no_visual = not rich_components["Confirm"].ask("Use visual progress frontend?", default=True)
			option_table = rich_components["Table"](title="Download Options")
			option_table.add_column("Option", style="cyan")
			option_table.add_column("Selected", style="bold green")
			option_table.add_row("Action", action)
			option_table.add_row("All dubs/subs in one MKV", "Yes" if all_languages else "No")
			option_table.add_row("Visual progress frontend", "Yes" if not no_visual else "No")
			option_table.add_row("Episodes selected", str(len(episode_urls)))
			console.print(option_table)
		else:
			all_languages = input("Download all dubs/subs into same MKV? [Y/n]: ").strip().lower() in {"", "y", "yes"}
			no_visual = input("Use visual progress frontend? [Y/n]: ").strip().lower() not in {"", "y", "yes"}
	else:
		all_languages = False
		no_visual = True

	return {
		"urls": episode_urls,
		"action": action,
		"all_languages": all_languages,
		"no_visual": no_visual,
	}


def _language_labels_for_episode(episode, provider_name: str, extract_menu_languages) -> list[str]:
	provider_data = episode.provider_data
	provider_dict = provider_data._data if hasattr(provider_data, "_data") else provider_data
	languages = extract_menu_languages(provider_name, provider_dict)

	if not languages:
		languages = [episode.selected_language]

	# Keep stable order while dropping duplicates.
	return list(dict.fromkeys(languages))


def _download_episode_all_languages(episode_url: str, resolve_provider, extract_menu_languages):
	provider = resolve_provider(episode_url)
	probe_episode = provider.episode_cls(url=episode_url)
	languages = _language_labels_for_episode(
		probe_episode,
		provider.name,
		extract_menu_languages,
	)

	print(f"\nEpisode: {episode_url}")
	print(f"Languages to merge: {', '.join(languages)}")

	for language in languages:
		episode = provider.episode_cls(url=episode_url, selected_language=language)
		with _suppress_download_noise():
			episode.download()


def _download_all_languages_for_object(obj, resolve_provider, extract_menu_languages):
	if hasattr(obj, "episodes"):
		for episode in obj.episodes:
			with _suppress_download_noise():
				_download_episode_all_languages(episode.url, resolve_provider, extract_menu_languages)
		return

	if hasattr(obj, "episode_number") and hasattr(obj, "provider_data"):
		_download_episode_all_languages(obj.url, resolve_provider, extract_menu_languages)
		return

	raise ValueError("--all-languages is only supported for episode, season, or series URLs.")


def _episode_list_for_object(obj):
	if hasattr(obj, "episodes"):
		return list(obj.episodes)
	return [obj]


def _episode_info(episode) -> tuple[str, str, str]:
	series_title = "Unknown Series"
	season_text = "Season ?"
	episode_text = "Episode ?"

	try:
		series_title = _clean_text(getattr(episode.series, "title", series_title) or series_title)
	except Exception:
		pass

	try:
		season_num = getattr(episode.season, "season_number", "?")
		season_text = f"Season {season_num}"
	except Exception:
		pass

	try:
		ep_num = getattr(episode, "episode_number", "?")
		ep_title = _clean_text(getattr(episode, "title", ""))
		ep_title = f" - {ep_title}" if ep_title else ""
		episode_text = f"Episode {ep_num}{ep_title}"
	except Exception:
		pass

	return series_title, season_text, episode_text


def _build_visual_jobs(objs, all_languages: bool, resolve_provider, extract_menu_languages):
	jobs = []
	for obj in objs:
		for episode in _episode_list_for_object(obj):
			series_title, season_text, episode_text = _episode_info(episode)
			provider = resolve_provider(episode.url)
			if all_languages:
				languages = _language_labels_for_episode(
					episode,
					provider.name,
					extract_menu_languages,
				)
			else:
				languages = [episode.selected_language]

			jobs.append(
				{
					"url": episode.url,
					"series_title": series_title,
					"season_text": season_text,
					"episode_text": episode_text,
					"languages": languages,
					"provider": provider,
				}
			)

	return jobs


def _download_with_visual_frontend(
	objs,
	all_languages: bool,
	resolve_provider,
	extract_menu_languages,
):
	if RICH_AVAILABLE is False:
		for obj in objs:
			if all_languages:
				with _suppress_download_noise():
					_download_all_languages_for_object(obj, resolve_provider, extract_menu_languages)
			else:
				for episode in _episode_list_for_object(obj):
					with _suppress_download_noise():
						episode.download()
		return

	rich_components = _load_rich_components()
	if not rich_components:
		for obj in objs:
			if all_languages:
				with _suppress_download_noise():
					_download_all_languages_for_object(obj, resolve_provider, extract_menu_languages)
			else:
				for episode in _episode_list_for_object(obj):
					with _suppress_download_noise():
						episode.download()
		return

	Console = rich_components["Console"]
	Panel = rich_components["Panel"]
	Progress = rich_components["Progress"]
	SpinnerColumn = rich_components["SpinnerColumn"]
	TextColumn = rich_components["TextColumn"]
	BarColumn = rich_components["BarColumn"]
	TimeElapsedColumn = rich_components["TimeElapsedColumn"]

	console = Console()
	jobs = _build_visual_jobs(objs, all_languages, resolve_provider, extract_menu_languages)
	if not jobs:
		return

	_suppress_aniworld_warning_logs()

	total_tracks = sum(len(job["languages"]) for job in jobs)
	max_workers = max(1, min(len(jobs), 10))  # Limit max workers to 10 for sanity.

	progress = Progress(
		SpinnerColumn(),
		TextColumn("[bold blue]{task.description}"),
		BarColumn(bar_width=None),
		TimeElapsedColumn(),
		console=console,
	)

	console.print(
		Panel(
			f"[bold]Episodes:[/bold] {len(jobs)}\n"
			f"[bold]Total language tracks:[/bold] {total_tracks}\n"
			f"[bold]Workers:[/bold] {max_workers}",
			title="Parallel Download",
			border_style="green",
		)
	)

	lock = threading.Lock()
	jobs_queue: queue.Queue = queue.Queue()
	for job in jobs:
		jobs_queue.put(job)

	failures: list[dict] = []

	def _worker(worker_id: int, worker_task_id: int):
		while True:
			try:
				job = jobs_queue.get_nowait()
			except queue.Empty:
				with lock:
					progress.update(worker_task_id, description=f"Worker {worker_id}: idle", total=1, completed=1)
				return

			provider = job["provider"]
			languages = job["languages"]

			with lock:
				progress.update(
					worker_task_id,
					description=(
						f"Worker {worker_id}: {job['series_title']} | "
						f"{job['season_text']} - {job['episode_text']}"
					),
					total=len(languages),
					completed=0,
				)

			try:
				for language in languages:
					with lock:
						progress.update(
							worker_task_id,
							description=(
								f"Worker {worker_id}: {job['series_title']} | "
								f"{job['season_text']} - {job['episode_text']} [{language}]"
							),
						)

					last_error: Exception | None = None
					provider_candidates = _provider_candidates_for_language(
						provider,
						job["url"],
						language,
					)

					success = False
					for candidate_provider in provider_candidates:
						try:
							with lock:
								progress.update(
									worker_task_id,
									description=(
										f"Worker {worker_id}: {job['series_title']} | "
										f"{job['season_text']} - {job['episode_text']} [{language}] ({candidate_provider})"
									),
								)

							active_episode = provider.episode_cls(
								url=job["url"],
								selected_language=language,
								selected_provider=candidate_provider,
							)
							active_episode.download()
							success = True
							break
						except Exception as exc:
							last_error = exc
							continue

					if not success:
						raise last_error or RuntimeError("Download failed for all providers")

					with lock:
						progress.advance(worker_task_id)
						progress.advance(overall_task)

				with lock:
					progress.advance(episode_task)

			except Exception as exc:
				with lock:
					failures.append({
						"job": job,
						"error": str(exc),
						"exception": exc,
					})
					progress.update(
						worker_task_id,
						description=(
							f"Worker {worker_id}: failed - "
							f"{job['season_text']} - {job['episode_text']}"
						),
					)
			finally:
				jobs_queue.task_done()

	with _suppress_download_noise(), progress:
		overall_task = progress.add_task("Overall", total=total_tracks, completed=0)
		episode_task = progress.add_task("Episodes", total=len(jobs), completed=0)
		worker_task_ids = [
			progress.add_task(f"Worker {i + 1}: waiting", total=1, completed=0)
			for i in range(max_workers)
		]

		threads = [
			threading.Thread(target=_worker, args=(i + 1, worker_task_ids[i]), daemon=True)
			for i in range(max_workers)
		]

		for t in threads:
			t.start()
		for t in threads:
			t.join()

		# Retry failed jobs
		if failures:
			console.print(
				Panel(
					f"[yellow]Retrying {len(failures)} failed downloads...[/yellow]",
					title="Retry Phase",
					border_style="yellow",
				)
			)

			retry_failures: list[dict] = []
			retry_workers = max(1, max_workers // 2)
			retry_task_ids = [
				progress.add_task(f"Retry {i + 1}: waiting", total=1, completed=0)
				for i in range(retry_workers)
			]

			def _retry_worker(worker_id: int, worker_task_id: int):
				while True:
					if not failures:
						break
					with lock:
						if not failures:
							break
						failed_item = failures.pop(0)

					job = failed_item["job"]
					provider = job["provider"]
					languages = job["languages"]

					with lock:
						progress.update(
							worker_task_id,
							description=(
								f"Retry {worker_id}: {job['series_title']} | "
								f"{job['season_text']} - {job['episode_text']}"
							),
							total=len(languages),
							completed=0,
						)

					try:
						for language in languages:
							with lock:
								progress.update(
									worker_task_id,
									description=(
										f"Retry {worker_id}: {job['series_title']} | "
										f"{job['season_text']} - {job['episode_text']} [{language}]"
									),
								)

							last_error: Exception | None = None
							provider_candidates = _provider_candidates_for_language(
								provider,
								job["url"],
								language,
							)

							success = False
							for candidate_provider in provider_candidates:
								try:
									with lock:
										progress.update(
											worker_task_id,
											description=(
												f"Retry {worker_id}: {job['series_title']} | "
												f"{job['season_text']} - {job['episode_text']} [{language}] ({candidate_provider})"
											),
										)

									active_episode = provider.episode_cls(
										url=job["url"],
										selected_language=language,
										selected_provider=candidate_provider,
									)
									active_episode.download()
									success = True
									break
								except Exception as exc:
									last_error = exc
									continue

							if not success:
								raise last_error or RuntimeError("Download failed for all providers")

							with lock:
								progress.advance(worker_task_id)
								progress.advance(overall_task)

						with lock:
							progress.advance(episode_task)

					except Exception as exc:
						with lock:
							retry_failures.append({
								"job": job,
								"error": str(exc),
								"exception": exc,
							})
							progress.update(
								worker_task_id,
								description=(
									f"Retry {worker_id}: FAILED (after retry) - "
									f"{job['season_text']} - {job['episode_text']}"
								),
							)

			retry_threads = [
				threading.Thread(target=_retry_worker, args=(i + 1, retry_task_ids[i]), daemon=True)
				for i in range(retry_workers)
			]

			for t in retry_threads:
				t.start()
			for t in retry_threads:
				t.join()

			failures = retry_failures

	if failures:
		failure_preview = "\n".join([
			f"{f['job']['series_title']} | {f['job']['season_text']} - {f['job']['episode_text']}: {f['error']}"
			for f in failures[:10]
		])
		raise RuntimeError(f"Some downloads failed (even after retry):\n{failure_preview}")


def main() -> int:
	_print_startup_banner()
	parser = _build_parser()
	args = parser.parse_args()
	_, resolve_provider, run_action = _load_aniworld_api()

	action = args.action
	all_languages = args.all_languages
	no_visual = args.no_visual

	if all_languages and action != "download":
		parser.error("--all-languages can only be used with --action download.")

	urls = [*args.urls, *_read_url_file(args.url_file)]
	if args.search and not args.no_interactive and not urls:
		wizard = _interactive_frontend_wizard(resolve_provider, initial_search=args.search)
		urls = wizard["urls"]
		action = wizard["action"]
		all_languages = wizard["all_languages"]
		no_visual = wizard["no_visual"]
	elif args.search:
		urls.append(_search_url_from_name(args.search, args.no_interactive))

	if not urls:
		wizard = _interactive_frontend_wizard(resolve_provider)
		urls = wizard["urls"]
		action = wizard["action"]
		all_languages = wizard["all_languages"]
		no_visual = wizard["no_visual"]

	extract_menu_languages = _load_menu_language_extractor() if all_languages else None
	objects = [_build_object(url, resolve_provider) for url in urls]

	if action == "download" and not no_visual:
		_download_with_visual_frontend(
			objects,
			all_languages=all_languages,
			resolve_provider=resolve_provider,
			extract_menu_languages=extract_menu_languages,
		)
		return 0

	for obj in objects:
		if all_languages:
			_download_all_languages_for_object(obj, resolve_provider, extract_menu_languages)
		else:
			with _suppress_download_noise():
				run_action(obj, action)

	return 0


if __name__ == "__main__":
	try:
		raise SystemExit(main())
	except Exception as exc:
		print(f"Error: {exc}", file=sys.stderr)
		raise SystemExit(1)

