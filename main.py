"""CLI utility to download and clean rap lyrics from Genius."""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Iterable

import lyricsgenius


EXCLUDED_TERMS: list[str] = ["(Remix)", "(Live)", "Freestyle", "(Skit)", "Intro"]
STOPWORDS: set[str] = {
    # Articles and demonstratives
    "a",
    "an",
    "the",
    "this",
    "that",
    "these",
    "those",
    # Pronouns and auxiliary verbs
    "am",
    "are",
    "be",
    "been",
    "being",
    "can",
    "could",
    "couldn't",
    "did",
    "didn't",
    "do",
    "does",
    "doesn't",
    "don't",
    "had",
    "hadn't",
    "has",
    "hasn't",
    "have",
    "haven't",
    "he",
    "her",
    "hers",
    "herself",
    "him",
    "himself",
    "his",
    "i",
    "is",
    "isn't",
    "it",
    "its",
    "itself",
    "may",
    "might",
    "me",
    "must",
    "my",
    "myself",
    "our",
    "ours",
    "ourselves",
    "she",
    "theirs",
    "them",
    "themselves",
    "they",
    "we",
    "were",
    "will",
    "won't",
    "would",
    "you",
    "your",
    "yours",
    "yourself",
    "yourselves",
    # Prepositions and conjunctions
    "about",
    "above",
    "after",
    "again",
    "against",
    "all",
    "also",
    "an",
    "and",
    "any",
    "as",
    "at",
    "before",
    "below",
    "between",
    "both",
    "but",
    "by",
    "during",
    "for",
    "from",
    "further",
    "if",
    "in",
    "into",
    "near",
    "nor",
    "of",
    "off",
    "on",
    "or",
    "other",
    "over",
    "own",
    "same",
    "so",
    "some",
    "such",
    "than",
    "their",
    "then",
    "there",
    "to",
    "too",
    "under",
    "until",
    "up",
    "very",
    "was",
    "what",
    "when",
    "where",
    "which",
    "while",
    "who",
    "whom",
    "why",
    "with",
    "would",
}


def sanitize_lyrics(text: str) -> str:
    """Strip section headers and simple punctuation noise from the lyrics."""

    no_sections = re.sub(r"\[.*?\]", "", text)
    # Remove straight and curly quotes to make the corpus easier to parse later.
    return re.sub(r"[\"'’]", "", no_sections)


def sanitize_filename(name: str) -> str:
    """Remove characters that do not play well in file names."""

    cleaned = re.sub(r"[\\/:*?\"<>|]", "", name)
    return cleaned.strip() or "untitled"


def iter_songs(
    client: lyricsgenius.Genius,
    artist_name: str,
    max_songs: int,
    sort: str = "popularity",
) -> Iterable[lyricsgenius.song.Song]:
    """Yield songs for an artist, raising on missing results."""

    artist = client.search_artist(artist_name, max_songs=max_songs, sort=sort)
    if artist is None or not artist.songs:
        raise RuntimeError(f"No songs found for artist '{artist_name}'.")

    yield from artist.songs


def download_lyrics(
    token: str,
    artist_name: str,
    output_dir: Path,
    max_songs: int = 50,
    timeout: int = 15,
) -> list[Path]:
    """Download lyrics for *artist_name* and write them to *output_dir*.

    Returns the list of file paths written to disk.
    """

    # Increase the default timeout (5s) to avoid frequent ReadTimeout errors when the
    # Genius API responds slowly and allow the CLI to override it if needed.
    genius = lyricsgenius.Genius(token, timeout=timeout)
    # Keep console output quiet while still respecting default retry behavior.
    genius.verbose = False
    # Drop bracketed markers such as [Chorus] to keep the text corpus clean.
    genius.remove_section_headers = True
    # Ignore non-song entries like skits or tracklists to reduce noise.
    genius.skip_non_songs = True
    # Avoid common variants that rarely contain unique lyrics.
    genius.excluded_terms = EXCLUDED_TERMS

    artist_folder = output_dir / sanitize_filename(artist_name)
    artist_folder.mkdir(parents=True, exist_ok=True)

    written_paths: list[Path] = []
    for song in iter_songs(genius, artist_name=artist_name, max_songs=max_songs):
        if not song.lyrics:
            # Occasionally a song object is missing lyrics; skip and keep going.
            continue

        cleaned_lyrics = sanitize_lyrics(song.lyrics)
        filename = sanitize_filename(song.title) + ".txt"
        file_path = artist_folder / filename
        file_path.write_text(cleaned_lyrics, encoding="utf-8")
        written_paths.append(file_path)
        print(f"Saved: {file_path}")

    if not written_paths:
        raise RuntimeError("No lyrics were saved; ensure the artist has songs with lyrics.")

    return written_paths


def build_corpus(files: Iterable[Path], artist_folder: Path) -> tuple[Path, str]:
    """Concatenate lyrics files into a single corpus file for the artist.

    Returns the corpus file path and the combined text to avoid re-reading from disk.
    """

    corpus_path = artist_folder / "corpus.txt"
    sorted_files = sorted(files)
    corpus_parts: list[str] = []
    for file_path in sorted_files:
        corpus_parts.append(file_path.read_text(encoding="utf-8"))
        corpus_parts.append("\n")

    corpus_text = "".join(corpus_parts)
    corpus_path.write_text(corpus_text, encoding="utf-8")

    return corpus_path, corpus_text


def calculate_word_stats(text: str) -> tuple[int, int, float]:
    """Return total words, unique words, and unique-per-1k score excluding stopwords."""

    words = re.findall(r"\b[a-zA-Z']+\b", text.lower())
    filtered_words = [word for word in words if word not in STOPWORDS]
    total_words = len(filtered_words)
    unique_words = len(set(filtered_words))
    unique_per_thousand = (unique_words / total_words * 1000) if total_words else 0.0

    return total_words, unique_words, unique_per_thousand


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artist", help="Artist name to fetch lyrics for")
    parser.add_argument(
        "--output-dir",
        default=Path("Lyrics"),
        type=Path,
        help="Directory where lyrics will be written (default: Lyrics)",
    )
    parser.add_argument(
        "--max-songs",
        type=int,
        default=50,
        help="Maximum number of songs to download (default: 50)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=15,
        help="Request timeout in seconds when talking to the Genius API (default: 15)",
    )
    parser.add_argument(
        "--token",
        default=os.environ.get("GENIUS_ACCESS_TOKEN"),
        help="Genius API access token (falls back to GENIUS_ACCESS_TOKEN env var)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or [])

    if not args.token:
        print("Error: Genius API token must be provided via --token or GENIUS_ACCESS_TOKEN", file=sys.stderr)
        return 1

    try:
        written_files = download_lyrics(
            token=args.token,
            artist_name=args.artist,
            output_dir=args.output_dir,
            max_songs=args.max_songs,
            timeout=args.timeout,
        )

        artist_folder = args.output_dir / sanitize_filename(args.artist)
        corpus_path, corpus_text = build_corpus(written_files, artist_folder)
        total_words, unique_words, unique_per_thousand = calculate_word_stats(corpus_text)

        print(f"Corpus created at: {corpus_path}")
        print(f"Total words (excluding stopwords): {total_words}")
        print(f"Unique words (excluding stopwords): {unique_words}")
        print(f"Unique words per 1,000 words: {unique_per_thousand:.2f}")
    except Exception as exc:  # noqa: BLE001 - provide clear CLI error output
        print(f"Failed to download lyrics: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
