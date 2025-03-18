from dataclasses import dataclass, field

@dataclass
class FireworkArgs:
    num_sparks: int = 60
    gravity: float = -0.004
    brightness_decay: float = 0.985
    flare_min_vel: float = 0.5
    flare_max_vel: float = 0.9
    c1: float = 120
    c2: float = 50

@dataclass
class AnimationState:
    """State of animations and neopixels"""
    state: str = "OFF"
    color: tuple = (255, 255, 255)
    effect: str = "SingleColor"
    brightness: float = 0.0


@dataclass
class SingleColorArgs:
    """Single Color mode options"""
    color: tuple = (255, 0, 0)

@dataclass
class GlitterRainbowArgs:
    """Glitter Rainbow Animation options"""
    glitter_ratio: float = 0.05

@dataclass
class FadeArgs:
    """Fade Animation options"""
    colora: tuple = (255, 0, 0)
    colorb: tuple = (0, 0, 0)


@dataclass
class FlashArgs:
    """Flash Animation options"""
    colora: tuple = (255, 0, 0)
    colorb: tuple = (0, 0, 0)
    speed: float = 25

@dataclass
class RandomArgs:
    """Random Animation options"""
    color: tuple = (255, 255, 255)

@dataclass
class WipeArgs:
    """Wipe Animation options"""
    colora: tuple = (255, 0, 0)
    colorb: tuple = (0, 0, 255)
    leds_iter: int = 1


@dataclass
class AnimationArgs:
    """Options for animations"""
    single_color: SingleColorArgs = field(default_factory=SingleColorArgs)
    glitter_rainbow: GlitterRainbowArgs = field(default_factory=GlitterRainbowArgs)
    fade: FadeArgs = field(default_factory=FadeArgs)
    flash: FlashArgs = field(default_factory=FlashArgs)
    wipe: WipeArgs = field(default_factory=WipeArgs)
    random: RandomArgs = field(default_factory=RandomArgs)
    firework: FireworkArgs = field(default_factory=FireworkArgs)
