from abc import ABC, abstractmethod


class IUpdatable(ABC):
    @abstractmethod
    def update(self) -> None:
        pass


    @abstractmethod
        pass


class IAvatar(IUpdatable, ABC):
    @property
    @abstractmethod
    def render_resource(self) -> any:
        pass
