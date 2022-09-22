from typing import Iterable

from pygame import Surface, draw, display, event, QUIT, time

from renders import Render, SurfaceKeeper, TypedResourceHandler, ResourcePack
from geometry import Vector
from pygame_resources import *
from tools import StoppingLoopUpdater, RGBAColor, LoopUpdater


class PygameSurfaceRender(SurfaceKeeper, Render):
    _resource_handler_wrapper_factory = TypedResourceHandler

    def __init__(self, surfaces: Iterable[Surface, ], background_color: RGBAColor = RGBAColor()):
        super().__init__(surfaces)
        self.background_color = background_color

    def _clear_surface(self, surface: any) -> None:
        surface.fill(tuple(self.background_color))

    @Render.resource_handler(supported_resource_type=Surface)
    def _handle_pygame_surface(resource_pack: ResourcePack, surface: Surface, render: 'PygameSurfaceRender') -> None:
        surface.blit(resource_pack.resource, resource_pack.point.coordinates)

    @Render.resource_handler(supported_resource_type=Polygon)
    def _handle_pygame_polygon(resource_pack: ResourcePack, surface: Surface, render: 'PygameSurfaceRender') -> None:
        draw.polygon(
            surface,
            tuple(resource_pack.resource.color),
            tuple(
                (resource_pack.point + vector_to_point).coordinates
                for vector_to_point in resource_pack.resource.points
            ),
            resource_pack.resource.border_width
        )

    @Render.resource_handler(supported_resource_type=Line)
    def _handle_pygame_line(resource_pack: ResourcePack, surface: Surface, render: 'PygameSurfaceRender') -> None:
        (draw.line if not resource_pack.resource.is_smooth else draw.aaline)(
            surface,
            tuple(resource_pack.resource.color),
            (resource_pack.resource.start_point + resource_pack.point).coordinates,
            (resource_pack.resource.end_point + resource_pack.point).coordinates,
            resource_pack.resource.border_width
        )

    @Render.resource_handler(supported_resource_type=Lines)
    def _handle_pygame_lines(resource_pack: ResourcePack, surface: Surface, render: 'PygameSurfaceRender') -> None:
        (draw.lines if not resource_pack.resource.is_smooth else draw.aalines)(
            surface,
            tuple(resource_pack.resource.color),
            resource_pack.resource.is_closed,
            tuple(
                (line_point + resource_pack.point).coordinates
                for line_point in resource_pack.resource.points
            ),
            resource_pack.resource.border_width
        )

    @Render.resource_handler(supported_resource_type=Circle)
    def _handle_pygame_circle(resource_pack: ResourcePack, surface: Surface, render: 'PygameSurfaceRender') -> None:
        draw.circle(
            surface,
            tuple(resource_pack.resource.color),
            resource_pack.point.coordinates,
            resource_pack.resource.radius,
            resource_pack.resource.border_width
        )

    @Render.resource_handler(supported_resource_type=Rectangle)
    def _handle_pygame_rect(resource_pack: ResourcePack, surface: Surface, render: 'PygameSurfaceRender') -> None:
        draw.rect(
            surface,
            tuple(resource_pack.resource.color),
            (
                *resource_pack.point.coordinates,
                resource_pack.resource.width,
                resource_pack.resource.height
            ),
            resource_pack.resource.border_width
        )

    @Render.resource_handler(supported_resource_type=Ellipse)
    def _handle_pygame_ellipse(resource_pack: ResourcePack, surface: Surface, render: 'PygameSurfaceRender') -> None:
        draw.ellipse(
            surface,
            tuple(resource_pack.resource.color),
            (
                *resource_pack.point.coordinates,
                resource_pack.resource.width,
                resource_pack.resource.height
            ),
            resource_pack.resource.border_width
        )

    @Render.resource_handler(supported_resource_type=Arc)
    def _handle_pygame_arc(resource_pack: ResourcePack, surface: Surface, render: 'PygameSurfaceRender') -> None:
        draw.arc(
            surface,
            tuple(resource_pack.resource.color),
            (
                *resource_pack.point.coordinates,
                resource_pack.resource.width,
                resource_pack.resource.height
            ),
            resource_pack.resource.start_angle,
            resource_pack.resource.stop_angle,
            resource_pack.resource.border_width
        )


class PygameKeyboardController:
    # Will be redone

    def __call__(self, loop: 'PygameLoopUpdater'):
        for event_ in event.get():
            if event_.type == QUIT:
                exit()

