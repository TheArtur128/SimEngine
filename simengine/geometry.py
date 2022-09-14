from dataclasses import dataclass
from typing import Iterable, Callable
from math import sqrt, modf

from pyoverload import overload

from tools import NumberRounder, ShiftNumberRounder, AccurateNumberRounder, Report, Divider
from errors.geometry_errors import UnableToDivideVectorIntoPointsError


@dataclass(frozen=True)
class Vector:
    coordinates: tuple[float | int] = tuple()

    @property
    def length(self) -> float:
        return sqrt(sum(coordinate**2 for coordinate in self.coordinates))

    def __add__(self, other: 'Vector') -> 'Vector':
        maximum_number_of_measurements = max((len(self.coordinates), len(other.coordinates)))

        return self.__class__(
            tuple(map(
                lambda first, second: first + second,
                self.get_normalized_to_measurements(maximum_number_of_measurements).coordinates,
                other.get_normalized_to_measurements(maximum_number_of_measurements).coordinates
            ))
        )

    def __sub__(self, other: 'Vector') -> 'Vector':
        return self + other.get_reflected_by_coordinates()

    def __len__(self) -> int:
        return len(self.coordinates)

    def get_normalized_to_measurements(
        self,
        number_of_measurements: int,
        default_measurement_point: int | float = 0
    ) -> 'Vector':
        measurement_difference = number_of_measurements - len(self.coordinates)

        return self.__class__(
            self.coordinates + (default_measurement_point,)*measurement_difference if measurement_difference > 0
            else self.coordinates[:number_of_measurements if number_of_measurements >= 0 else 0]
        )

    def get_reflected_by_coordinates(
        self,
        coordinate_indexes: Iterable[int, ] | None = None
    ) -> 'Vector':
        if coordinate_indexes is None:
            coordinate_indexes = range(len(self.coordinates))

        return self.__class__(tuple(
            coordinate * (-1 if coordinate_index in coordinate_indexes else 1)
            for coordinate_index, coordinate in enumerate(self.coordinates)
        ))

    def get_rounded_by(self, rounder: NumberRounder) -> 'Vector':
        return self.__class__(tuple(
            rounder(coordinate)
            for coordinate in self.coordinates
        ))


@dataclass
class VirtualVector:
    start_point: Vector
    end_point: Vector

    @property
    def value(self) -> Vector:
        return self.end_point - self.start_point

    def get_rounded_by(self, rounder: NumberRounder) -> 'VirtualVector':
        return self.__class__(
            self.start_point.get_rounded_by(rounder),
            self.end_point.get_rounded_by(rounder)
        )


class VectorDivider(Divider):
    def __init__(self, distance_between_points: int | float, rounder: NumberRounder):
        self.distance_between_points = distance_between_points
        self.rounder = rounder

    def is_possible_to_divide(self, data: Vector) -> Report:
        return Report.create_error_report(
            UnableToDivideVectorIntoPointsError(
                f"Can't divide vector {vector} into points with length 0"
            )
        ) if data.value.length == 0 else super().is_possible_to_divide(data)

    def _divide(self, vector: VirtualVector) -> None:
        factor = self.rounder(vector.value.length / self.distance_between_points)

        vector_to_next_point = Vector(tuple(
            coordinate / factor for coordinate in vector.value.coordinates
        ))

        number_of_points_to_create = vector.value.length / vector_to_next_point.length + 1

        if number_of_points_to_create <= 0 or modf(number_of_points_to_create)[0]:
            raise UnableToDivideVectorIntoPointsError(
                "Can't divide vector {vector} into {point_number} points by segment {segment}".format(
                    vector=vector,
                    point_number=number_of_points_to_create,
                    segment=vector_to_next_point
                )
            )

        return self.__create_points(vector.start_point, number_of_points_to_create, vector_to_next_point)

    def __create_points(
        self,
        start_point: Vector,
        number_of_points_to_create: int,
        vector_to_next_point: Vector
    ) -> tuple[Vector, ]:
        created_points = [start_point]

        for created_point_index in range(1, int(number_of_points_to_create)):
            created_points.append(
                created_points[created_point_index - 1] + vector_to_next_point
            )

        return tuple(
            map(lambda point: point.get_rounded_by(self.rounder), created_points)
        )


class Line:
    _vector_divider_factory: Callable[['Line'], VectorDivider] = (
        lambda _: VectorDivider(1, ShiftNumberRounder(AccurateNumberRounder(), 2))
    )

    def __init__(self, first_point: Vector, second_point: Vector):
        self._vector_divider = self._vector_divider_factory()
        self._rounder = self._vector_divider.rounder

        self.__first_point = first_point
        self.__second_point = second_point

        self._update_all_available_points()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__} between {self.first_point} and {self.second_point}"

    @property
    def first_point(self) -> Vector:
        return self.__first_point

    @first_point.setter
    def first_point(self, new_point: Vector) -> None:
        self._update_all_available_points()
        self.__first_point = new_point

    @property
    def second_point(self) -> Vector:
        return self.__second_point

    @second_point.setter
    def second_point(self, new_point: Vector) -> None:
        self._update_all_available_points()
        self.__second_point = new_point

    @property
    def all_available_points(self) -> tuple[Vector, ]:
        return self.__all_available_points

    @overload
    def __contains__(self, point: Vector) -> bool:
        return self.is_point_inside(point)

    @overload
    def __contains__(self, vector: VirtualVector) -> bool:
        return self.is_vector_passes(vector)

    def is_vector_passes(self, vector: VirtualVector) -> bool:
        rounded_vector = vector.get_rounded_by(self._rounder)

        return any(
            self.is_point_inside(point)
            for point in self._vector_divider(rounded_vector)
        )

    def is_point_inside(self, point: Vector) -> bool:
        return point.get_rounded_by(self._rounder) in self.__all_available_points

        self.__first_point, self.__second_point = map(
            lambda vector: vector.get_rounded_by(self._rounder),
            (self.__first_point, self.__second_point)
        )

    def _update_all_available_points(self) -> None:
        self.__all_available_points = self._vector_divider(
            VirtualVector(self.first_point, self.second_point)
        )
