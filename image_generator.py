"""
Strava Streams -> Landscape PNG with basemap tiles (Contextily)

Install:
  pip install requests matplotlib contextily pyproj shapely

Usage:
  python strava_streams_to_map.py <ACCESS_TOKEN> <ACTIVITY_ID> <OUTPUT.png> [zoom]

Example:
  python strava_streams_to_map.py "$STRAVA_TOKEN" 1234567890 ./exports/1234567890_map.png
  python strava_streams_to_map.py "$STRAVA_TOKEN" 1234567890 ./exports/1234567890_map.png 14
"""

import math
import sys
from pathlib import Path

import requests
import matplotlib.pyplot as plt

import contextily as ctx
from pyproj import Transformer
from shapely.geometry import LineString


def fetch_strava_latlng_stream(
    access_token: str,
    activity_id: int,
    *,
    timeout_seconds: int = 30,
) -> tuple[list[float], list[float]]:
    """
    Fetch Strava latlng stream and return (lats, lons).
    """
    url = f"https://www.strava.com/api/v3/activities/{activity_id}/streams"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"keys": "latlng", "key_by_type": "true"}

    resp = requests.get(url, headers=headers, params=params, timeout=timeout_seconds)
    resp.raise_for_status()

    payload = resp.json()
    points = (payload.get("latlng") or {}).get("data") or []
    if not points:
        raise ValueError("No latlng stream found (activity likely has no GPS track, or token lacks access).")

    lats = [p[0] for p in points]
    lons = [p[1] for p in points]
    return lats, lons


def strava_streams_to_landscape_map_image(
    lats: list[float],
    lons: list[float],
    output_image: str | Path,
    *,
    max_points: int = 6000,
    route_colour: str = "#FC4C02",
    route_width: float = 5.0,
    route_alpha: float = 0.95,
    tile_provider=ctx.providers.CartoDB.Positron,
    zoom: int | None = None,  # IMPORTANT: omitted when None (older contextily compatibility)
    pad_ratio: float = 0.12,
    dpi: int = 200,  # 9.6x5.4 inches @200dpi ~= 1920x1080
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


def strava_activity_to_landscape_map_png(
    access_token: str,
    activity_id: int,
    output_image: str | Path,
    *,
    zoom: int | None = None,
) -> Path:
    """
    Convenience wrapper: fetch streams from Strava and render map image.
    """
    lats, lons = fetch_strava_latlng_stream(access_token, activity_id)
    return strava_streams_to_landscape_map_image(lats, lons, output_image, zoom=zoom)


def main(argv: list[str]) -> int:
    if len(argv) < 4:
        print("Usage: python strava_streams_to_map.py <ACCESS_TOKEN> <ACTIVITY_ID> <OUTPUT.png> [zoom]")
        return 2

    access_token = argv[1]
    activity_id = int(argv[2])
    output = argv[3]

    zoom = None
    if len(argv) >= 5 and argv[4].strip():
        zoom = int(argv[4])

    saved = strava_activity_to_landscape_map_png(
        access_token=access_token,
        activity_id=activity_id,
        output_image=output,
        zoom=zoom,
    )
    print(f"Saved: {saved}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
