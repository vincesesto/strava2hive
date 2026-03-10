"""
Strava -> Share image generator (Landscape)

Behaviour:
- If the activity has GPS (latlng stream): render a LANDSCAPE map image with basemap tiles + route line + title
- If the activity has NO GPS: render a clean LANDSCAPE stats card

Dependencies:
  pip install requests matplotlib contextily pyproj shapely

Usage:
  python strava_share_image.py <ACCESS_TOKEN> <ACTIVITY_ID> <OUTPUT.png> [zoom]

Examples:
  python strava_share_image.py "$STRAVA_TOKEN" 1234567890 ./exports/1234567890.png
  python strava_share_image.py "$STRAVA_TOKEN" 1234567890 ./exports/1234567890.png 14
"""

import math
import sys
from datetime import datetime
from pathlib import Path

import requests
import matplotlib.pyplot as plt

import contextily as ctx
from pyproj import Transformer
from shapely.geometry import LineString


# ----------------------------
# Strava API helpers
# ----------------------------

def fetch_strava_activity(
    access_token: str,
    activity_id: int,
    *,
    timeout_seconds: int = 30,
) -> dict:
    """
    Fetch activity details (name, times, distance, etc.)
    GET /api/v3/activities/{id}
    """
    url = f"https://www.strava.com/api/v3/activities/{activity_id}"
    headers = {"Authorization": f"Bearer {access_token}"}

    resp = requests.get(url, headers=headers, timeout=timeout_seconds)
    resp.raise_for_status()
    return resp.json()


def fetch_strava_latlng_stream(
    access_token: str,
    activity_id: int,
    *,
    timeout_seconds: int = 30,
) -> tuple[list[float], list[float]]:
    """
    Fetch Strava latlng stream and return (lats, lons).
    Raises ValueError if no GPS stream data exists.
    """
    url = f"https://www.strava.com/api/v3/activities/{activity_id}/streams"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"keys": "latlng", "key_by_type": "true"}

    resp = requests.get(url, headers=headers, params=params, timeout=timeout_seconds)
    resp.raise_for_status()

    payload = resp.json()
    points = (payload.get("latlng") or {}).get("data") or []
    if not points:
        raise ValueError("No latlng stream found (no GPS track).")

    lats = [p[0] for p in points]
    lons = [p[1] for p in points]
    return lats, lons


def has_gps_data(
    access_token: str,
    activity_id: int,
    *,
    timeout_seconds: int = 30,
) -> bool:
    """
    Robust GPS check using the streams API.
    Returns True if latlng stream exists and is non-empty.
    """
    try:
        lats, lons = fetch_strava_latlng_stream(access_token, activity_id, timeout_seconds=timeout_seconds)
        return len(lats) > 0 and len(lons) > 0
    except ValueError:
        return False


# ----------------------------
# Rendering helpers
# ----------------------------

def _format_distance_km(distance_metres: float | int | None) -> str:
    if not distance_metres:
        return "—"
    return f"{distance_metres / 1000:.2f} km"


def _format_duration(seconds: int | float | None) -> str:
    if seconds is None:
        return "—"
    seconds = int(seconds)
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h > 0:
        return f"{h:d}:{m:02d}:{s:02d}"
    return f"{m:d}:{s:02d}"


def _format_start_datetime(activity: dict) -> str:
    """
    Uses start_date_local if present; falls back to start_date.
    Example output: '10 Mar 2026, 07:14'
    """
    s = activity.get("start_date_local") or activity.get("start_date")
    if not s:
        return "—"

    # Strava returns ISO8601 like '2026-03-10T20:14:05Z' or without Z for local
    s_norm = s.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(s_norm)
    except ValueError:
        return s

    return dt.strftime("%d %b %Y, %H:%M")


def render_activity_stats_card(
    activity: dict,
    output_image: str | Path,
    *,
    dpi: int = 200,
    figsize: tuple[float, float] = (9.6, 5.4),  # ~1920x1080 at 200dpi
    background_colour: str = "white",
    accent_colour: str = "#FC4C02",
    text_colour: str = "#111111",
    subtle_colour: str = "#666666",
) -> Path:
    """
    Render a clean, landscape activity summary card.

    Card contents:
    - Title: activity name
    - Key stats (big text): Distance, Elapsed / Moving time
    - Date + start time
    """
    output_image = Path(output_image)
    output_image.parent.mkdir(parents=True, exist_ok=True)

    title = activity.get("name") or (activity.get("type") or "Activity")
    distance = _format_distance_km(activity.get("distance"))
    moving = _format_duration(activity.get("moving_time"))
    elapsed = _format_duration(activity.get("elapsed_time"))
    start_dt = _format_start_datetime(activity)

    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    fig.patch.set_facecolor(background_colour)
    ax.set_facecolor(background_colour)
    ax.set_axis_off()

    # Header
    ax.text(
        0.06, 0.86, title,
        transform=ax.transAxes,
        fontsize=30,
        fontweight="bold",
        color=text_colour,
        ha="left",
        va="top",
    )

    # Subheader: date/time
    ax.text(
        0.06, 0.78, start_dt,
        transform=ax.transAxes,
        fontsize=14,
        color=subtle_colour,
        ha="left",
        va="top",
    )

    # Accent line
    ax.plot([0.06, 0.94], [0.73, 0.73], transform=ax.transAxes, color=accent_colour, linewidth=3)

    # Key stats blocks
    ax.text(0.06, 0.62, "Distance", transform=ax.transAxes, fontsize=14, color=subtle_colour, ha="left", va="top")
    ax.text(
        0.06, 0.56, distance,
        transform=ax.transAxes,
        fontsize=34,
        fontweight="bold",
        color=text_colour,
        ha="left",
        va="top",
    )

    ax.text(0.55, 0.62, "Moving time", transform=ax.transAxes, fontsize=14, color=subtle_colour, ha="left", va="top")
    ax.text(
        0.55, 0.56, moving,
        transform=ax.transAxes,
        fontsize=30,
        fontweight="bold",
        color=text_colour,
        ha="left",
        va="top",
    )

    ax.text(0.55, 0.46, "Elapsed time", transform=ax.transAxes, fontsize=14, color=subtle_colour, ha="left", va="top")
    ax.text(
        0.55, 0.40, elapsed,
        transform=ax.transAxes,
        fontsize=30,
        fontweight="bold",
        color=text_colour,
        ha="left",
        va="top",
    )

    ax.text(
        0.06, 0.08, "No GPS track available for this activity.",
        transform=ax.transAxes,
        fontsize=12,
        color=subtle_colour,
        ha="left",
        va="bottom",
    )

    fig.savefig(output_image, bbox_inches="tight", pad_inches=0, facecolor=background_colour)
    plt.close(fig)
    return output_image


def render_route_map_image(
    lats: list[float],
    lons: list[float],
    output_image: str | Path,
    *,
    title: str | None = None,  # <-- TITLE OVERLAY
    max_points: int = 6000,
    route_colour: str = "#FC4C02",
    route_width: float = 5.0,
    route_alpha: float = 0.95,
    tile_provider=ctx.providers.CartoDB.Positron,
    zoom: int | None = None,  # IMPORTANT: omitted when None (older contextily compatibility)
    pad_ratio: float = 0.12,
    dpi: int = 200,
    add_start_finish: bool = True,
) -> Path:
    """
    Render a landscape PNG with basemap + route line.
    Input lats/lons are EPSG:4326.
    """
    output_image = Path(output_image)
    output_image.parent.mkdir(parents=True, exist_ok=True)

    if not lats or not lons:
        raise ValueError("Empty lat/lon arrays")

    # Downsample for performance / tile fetching
    n = len(lats)
    if n > max_points:
        step = math.ceil(n / max_points)
        lats = lats[::step]
        lons = lons[::step]

    if len(lats) < 2:
        raise ValueError(f"Not enough points to render route: {len(lats)} point(s)")

    # Project to Web Mercator (EPSG:3857) for Contextily tiles
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
    xs, ys = transformer.transform(lons, lats)

    # Compute bounds + padding (in metres)
    line = LineString(zip(xs, ys))
    minx, miny, maxx, maxy = line.bounds

    dx = maxx - minx
    dy = maxy - miny
    pad_x = (dx if dx > 0 else 100) * pad_ratio
    pad_y = (dy if dy > 0 else 100) * pad_ratio

    # Landscape canvas
    figsize = (9.6, 5.4)
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    ax.set_axis_off()

    ax.set_xlim(minx - pad_x, maxx + pad_x)
    ax.set_ylim(miny - pad_y, maxy + pad_y)

    # Basemap (do NOT pass zoom if None)
    basemap_kwargs = dict(
        source=tile_provider,
        crs="EPSG:3857",
        attribution=False,
    )
    if zoom is not None:
        basemap_kwargs["zoom"] = zoom

    ctx.add_basemap(ax, **basemap_kwargs)

    # Title overlay (top-left) with a translucent background for readability
    if title:
        ax.text(
            0.02, 0.98,
            title,
            transform=ax.transAxes,
            ha="left",
            va="top",
            fontsize=18,
            fontweight="bold",
            color="#111111",
            bbox=dict(
                boxstyle="round,pad=0.35",
                facecolor="white",
                edgecolor="none",
                alpha=0.85,
            ),
            zorder=10,
        )

    # Route "halo" + route line for contrast
    ax.plot(xs, ys, color="white", linewidth=route_width + 3.0, alpha=0.85, zorder=4)
    ax.plot(xs, ys, color=route_colour, linewidth=route_width, alpha=route_alpha, zorder=5)

    # Start/finish markers
    if add_start_finish:
        ax.scatter([xs[0]], [ys[0]], s=90, c="#2ECC71", edgecolors="white", linewidths=2, zorder=6)
        ax.scatter([xs[-1]], [ys[-1]], s=90, c="#E74C3C", edgecolors="white", linewidths=2, zorder=6)

    fig.savefig(output_image, bbox_inches="tight", pad_inches=0)
    plt.close(fig)
    return output_image


def strava_activity_to_share_image(
    access_token: str,
    activity_id: int,
    output_image: str | Path,
    *,
    zoom: int | None = None,
) -> Path:
    """
    Main entrypoint:
    - If GPS exists: render map route + title
    - Else: render stats card
    """
    activity = fetch_strava_activity(access_token, activity_id)
    title = activity.get("name") or (activity.get("type") or "Activity")

    if has_gps_data(access_token, activity_id):
        lats, lons = fetch_strava_latlng_stream(access_token, activity_id)
        return render_route_map_image(
            lats,
            lons,
            output_image,
            zoom=zoom,
            title=title,
        )
    else:
        return render_activity_stats_card(activity, output_image)


# ----------------------------
# CLI
# ----------------------------

def main(argv: list[str]) -> int:
    if len(argv) < 4:
        print("Usage: python strava_share_image.py <ACCESS_TOKEN> <ACTIVITY_ID> <OUTPUT.png> [zoom]")
        return 2

    access_token = argv[1]
    activity_id = int(argv[2])
    output = argv[3]

    zoom = None
    if len(argv) >= 5 and argv[4].strip():
        zoom = int(argv[4])

    saved = strava_activity_to_share_image(
        access_token=access_token,
        activity_id=activity_id,
        output_image=output,
        zoom=zoom,
    )
    print(f"Saved: {saved}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
