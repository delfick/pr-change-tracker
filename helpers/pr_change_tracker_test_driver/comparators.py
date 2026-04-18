import attrs


@attrs.mutable
class IsInstance:
    _expect: type

    _got: object = attrs.field(init=False)

    @classmethod
    def using[T_Expect](cls, _expect: type[T_Expect], /) -> T_Expect:
        return cls(_expect)  # type: ignore[return-value]

    def __eq__(self, other: object) -> bool:
        self._got = other
        return isinstance(other, self._expect)

    def __repr__(self) -> str:
        if hasattr(self, "_got"):
            return repr(self._got)
        else:
            return f"<IsInstance {self._expect}>"
