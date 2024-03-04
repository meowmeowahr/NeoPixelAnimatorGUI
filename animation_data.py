from dataclasses import dataclass, field


@dataclass
class SingleColorArgs:
    "Single Color mode options"
    color: tuple = (255, 0, 0)


@dataclass
class FadeArgs:
    "Fade Animation options"
    colora: tuple = (255, 0, 0)
    colorb: tuple = (0, 0, 0)


@dataclass
class FlashArgs:
    "Flash Animation options"
    colora: tuple = (255, 0, 0)
    colorb: tuple = (0, 0, 0)
    speed: float = 25


@dataclass
class WipeArgs:
    "Wipe Animation options"
    colora: tuple = (255, 0, 0)
    colorb: tuple = (0, 0, 255)
    leds_iter: int = 1


@dataclass
class AnimationArgs:
    "Options for animations"
    single_color: SingleColorArgs = field(default_factory=SingleColorArgs)
    fade: FadeArgs = field(default_factory=FadeArgs)
    flash: FlashArgs = field(default_factory=FlashArgs)
    wipe: WipeArgs = field(default_factory=WipeArgs)