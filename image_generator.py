import math
import sys
from pathlib import Path
import gpxpy
import matplotlib.pyplot as plt
import contextily as ctx
from pyproj import Transformer
from shapely.geometry import LineString

def gpx_to_landscape_map_image(
    gpx_file: str | Path,
    output_image: str | Path,
    *,
    max_points: int = 6000,
    route_colour: str = "#FC4C02",  # Strava-ish orange
    route_width: float = 5.0,
    route_alpha: float = 0.95,
    tile_provider=ctx.providers.CartoDB.Positron,  # clean/light for sharing
    zoom: int | None = None,  # IMPORTANT: will be omitted when None (older contextily compatibility)
    pad_ratio: float = 0.12,
    dpi: int = 200,  # 9.6x5.4 inches @200 dpi ≈ 1920x1080
    add_start_finish: bool = True,
) -> Path:
    """
    Render a GPX route as a shareable LANDSCAPE map image (PNG recommended).
    """
    gpx_file = Path(gpx_file)
    output_image = Path(output_image)
    output_image.parent.mkdir(parents=True, exist_ok=True)

    # 1) Parse GPX points
    with gpx_file.open("r", encoding="utf-8") as f:
        gpx = gpxpy.parse(f)

    lats: list[float] = []
    lons: list[float] = []
    for track in gpx.tracks:
        for segment in track.segments:
            for p in segment.points:
                if p.latitude is not None and p.longitude is not None:
                    lats.append(p.latitude)
                    lons.append(p.longitude)

    if not lats:
        raise ValueError(f"No track points found in GPX: {gpx_file}")

    # 2) Downsample to keep plotting reasonable
    n = len(lats)
    if n > max_points:
        step = math.ceil(n / max_points)
        lats = lats[::step]
        lons = lons[::step]

    # 3) Project to Web Mercator (EPSG:3857) for basemap tiles
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
    xs, ys = transformer.transform(lons, lats)

    # 4) Compute bounds + padding
    line = LineString(zip(xs, ys))
    minx, miny, maxx, maxy = line.bounds

    dx = maxx - minx
    dy = maxy - miny
    pad_x = (dx if dx > 0 else 100) * pad_ratio
    pad_y = (dy if dy > 0 else 100) * pad_ratio

    # 5) Landscape canvas (≈1920x1080)
    figsize = (9.6, 5.4)
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    ax.set_axis_off()

    ax.set_xlim(minx - pad_x, maxx + pad_x)
    ax.set_ylim(miny - pad_y, maxy + pad_y)

    # 6) Basemap (UPDATED: do not pass zoom if None)
    basemap_kwargs = dict(
        source=tile_provider,
        crs="EPSG:3857",
        attribution=False,
    )
    if zoom is not None:
        basemap_kwargs["zoom"] = zoom

    ctx.add_basemap(ax, **basemap_kwargs)

    # 7) Route overlay (white halo + coloured line for contrast)
    ax.plot(xs, ys, color="white", linewidth=route_width + 3.0, alpha=0.85, zorder=4)
    ax.plot(xs, ys, color=route_colour, linewidth=route_width, alpha=route_alpha, zorder=5)

    # 8) Start/finish markers
    if add_start_finish and len(xs) >= 2:
        ax.scatter([xs[0]], [ys[0]], s=90, c="#2ECC71", edgecolors="white", linewidths=2, zorder=6)
        ax.scatter([xs[-1]], [ys[-1]], s=90, c="#E74C3C", edgecolors="white", linewidths=2, zorder=6)

    fig.savefig(output_image, bbox_inches="tight", pad_inches=0)
    plt.close(fig)
    return output_image


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print("Usage: python gpx_to_landscape_map.py <input.gpx> <output.png> [zoom]")
        print("Example: python gpx_to_landscape_map.py activity.gpx activity.png 14")
        return 2

    gpx_path = argv[1]
    out_path = argv[2]

    zoom = None
    if len(argv) >= 4 and argv[3].strip():
        zoom = int(argv[3])

    saved = gpx_to_landscape_map_image(
        gpx_file=gpx_path,
        output_image=out_path,
        zoom=zoom,  # omit in ctx.add_basemap when None
    )

    print(f"Saved: {saved}")
    return 0


#out = gpx_to_landscape_map_image(
#    gpx_file="ATF-bikeCourse.gpx",
#    output_image="ATF-bikeCourse.png",
#)
