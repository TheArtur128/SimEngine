from abc import ABC
from dataclasses import dataclass
from typing import Callable, Iterable

from beautiful_repr import StylizedMixin, Field

from simengine.core import PositionalUnit
from simengine.geometry import Vector
from simengine.renders import ResourcePack
from simengine.interfaces import IAvatar
from simengine.errors.avatar_errors import AnimationAlreadyFinishedError


class Avatar(IAvatar, ABC):
    def __init__(self, unit: PositionalUnit):
        self._unit = unit

    @property
    def unit(self) -> PositionalUnit:
        return self._unit


class SingleResourcePackAvatar(Avatar, ABC):
    _main_resource_pack: ResourcePack

    @property
    def render_resource_packs(self) -> tuple[ResourcePack, ]:
        return (self._main_resource_pack, )

    def update(self) -> None:
        self._main_resource_pack.point = self.unit.position


class ResourceAvatar(SingleResourcePackAvatar, StylizedMixin, ABC):
    _repr_fields = (Field('resource'), )
    _resource_factory: Callable[['ResourceAvatar'], any]
    _resource_pack_factory: Callable[[any, Vector], ResourcePack] = ResourcePack

    def __init__(self, unit: PositionalUnit):
        super().__init__(unit)
        self._main_resource_pack = self._resource_pack_factory(
            self._resource_factory(self),
            self.unit.position
        )

    @property
    def render_resource(self) -> any:
        return self._main_resource_pack.resource


class PrimitiveAvatar(ResourceAvatar, ABC):
    def __init__(self, unit: PositionalUnit, resource: any):
        self._resource_factory = lambda _: resource
        super().__init__(unit)

    @property
    def render_resource(self) -> any:
         return ResourceAvatar.render_resource.fget(self)

    @render_resource.setter
    def render_resource(self, render_resource: any) -> None:
        self._main_resource_pack.resource = render_resource


@dataclass
class Sprite:
    resource: any
    max_stay_ticks: int

    def __post_init__(self):
        self.real_stay_ticks = self.max_stay_ticks


class Animation(SingleResourcePackAvatar, ABC):
    _sprites: tuple[Sprite, ]
    _current_sprite_index: int = 0

    def __init__(self, unit: PositionalUnit):
        super().__init__(unit)
        self._update_main_resource_pack()

    def update(self) -> None:
        super().update()

        if self.is_finished():
            self._handle_finish()

        self._update_main_resource_pack()

        self._active_sprite.real_stay_ticks -= 1

        if self._active_sprite.real_stay_ticks <= 0:
            self._current_sprite_index += 1

    def is_finished(self) -> bool:
        return (
            self._current_sprite_index >= len(self._sprites) - 1
            and self._active_sprite.real_stay_ticks <= 0
        )

    @property
    def _active_sprite(self) -> Sprite:
        return self._sprites[self._current_sprite_index]

    def _update_main_resource_pack(self) -> None:
        self._main_resource_pack = ResourcePack(
            self._sprites[self.__current_sprite_index].resource,
            self.unit.position
        )

    def _handle_finish(self) -> None:
        raise AnimationAlreadyFinishedError(f"Animation {self} already finished")


class CustomAnimation(Animation):
    def __init__(self, unit: PositionalUnit, sprites: Iterable[Sprite]):
        super().__init__(unit)
        self._sprites = tuple(sprites)


class EndlessAnimation(Animation, ABC):
    def _handle_finish(self) -> None:
        self._current_sprite_index = 0

        for sprite in self._sprites:
            sprite.real_stay_ticks = sprite.max_stay_ticks


class CustomEndlessAnimation(EndlessAnimation, CustomAnimation):
    pass


class AnimationAvatar(Avatar, ABC):
    _default_animation_factory: Callable[[PositionalUnit], EndlessAnimation]

    def __init__(self, unit: PositionalUnit):
        super().__init__(unit)
        self._current_animation = self._default_animation = self._default_animation_factory(unit)

    @property
    def render_resource_packs(self) -> tuple[ResourcePack, ]:
        return self._current_animation.render_resource_packs

    def update(self) -> None:
        self._current_animation.update()


class TopicAnimationAvatar(AnimationAvatar, ABC):
    _animation_factory_by_topic: dict[str, Callable[[PositionalUnit], EndlessAnimation]]

    def __init__(self, unit: PositionalUnit):
        super().__init__(unit)

        self._animation_by_topic = {
            topic: animation_factory(unit)
            for topic, animation_factory in self._animation_factory_by_topic.items()
        }

    def update(self) -> None:
        if (
            self._default_animation is not self._current_animation
            and self._current_animation.is_finished()
        ):
            self._current_animation = self._default_animation

        super().update()

    def activate_animation_by_topic(self, topic: str) -> None:
        self._current_animation = self._animation_by_topic[topic]


class CustomTopicAnimationAvatar(TopicAnimationAvatar):
    def __init__(
        self,
        unit: PositionalUnit,
        animation_factory_by_topic: dict[str, Callable[[PositionalUnit], EndlessAnimation]]
    ):
        self._animation_factory_by_topic = animation_factory_by_topic
        super().__init__(unit)
