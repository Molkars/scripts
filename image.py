import sys
from types import SimpleNamespace
from PIL import Image, ImageEnhance
from cli import Command, Flag, Param, parse_args, print_help

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def cmd_help(input):
    pass

def cmd_brightness(input: SimpleNamespace) -> int:
    image = input.image
    brightness = input.brightness

    enhancer = ImageEnhance.Brightness(image)
    result = enhancer.enhance(brightness)

    if input.output:
        result.save(input.output[0])
    else:
        result.show()

    return 0

if __name__ == '__main__':
    COMMANDS = [
        Command("help", "print help")
            .short("-h")
            .long("--help")
            .arg(Param("command").optional()),
        Command("brightness", "adjust the brightness of an image")
            .arg(Param("image", "the file to open").parser(Image.open))
            .arg(Param("brightness", "the new brightness value, (0.0..1.0 is the standard range)")
                 .parser(float))
            .arg(Flag("output", "the output file path")
                 .short("-o")
                 .long("--output")
                 .valued()),
    ]

    try:
        args = parse_args(COMMANDS)
    except (InterruptedError, KeyboardInterrupt) as err:
        sys.exit(1)
    except ValueError as err:
        print(f"error: {err.args[0]}", file=sys.stderr)
        print_help(
                "image.py",
                "A simple CLI for image processing",
                COMMANDS,
        )
        sys.exit(1)
    
    cmd = args.command()
    vals = args.values()
    if cmd == "help":
        print(f"help for: {vals.command or '<nil>'}")
        print("todo: ...")
        exit(1)
    if cmd == "brightness":
        exit(cmd_brightness(vals))

