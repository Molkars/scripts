import traceback
import re
from types import SimpleNamespace
from typing import Any, Callable, List, Literal, Optional, Union

def typecheck(val, ty):
    if not isinstance(val, ty):
        stack = traceback.extract_stack()
        try:
            _, _, _, code = stack[-2]
            pattern_match = re.compile(r'\((.*?)\).*$').search(code)
            if pattern_match is not None:
                vars_name = pattern_match.groups()[0]
            else:
                vars_name = "<unknown>"
        except ValueError:
            vars_name = "<unknown>"
        raise TypeError(f"{vars_name} (of type {str(type(val))!r}) must be of type {str(ty)!r}!!")

class Command:
    _name: str
    _description: Optional[str]
    _short: List[str]
    _long: List[str]
    _disable_name: bool
    _flags: List['Flag']
    _params: List['Param']

    def __init__(self, name: str, description: Optional[str] = None):
        typecheck(name, str)
        typecheck(description, Optional[str])

        if not name.strip():
            raise ValueError("name must be a non-empty string!")

        self._name = name
        self._description = description
        self._short = list() 
        self._long = list() 
        self._disable_name = False
        self._flags = list()
        self._params = list()

    def short(self, short: str) -> 'Command':
        typecheck(short, str)
        short = short.strip()
        if short.startswith("--"):
            raise ValueError(f"command {self.name()}: short-flag cannot start with '--'")
        if not short.startswith("-"):
            raise ValueError(f"command {self.name()}: short-flag must start with '-'")
        if len(short) != 2:
            raise ValueError(f"command {self.name()}: short-flags must be only 2 characters long!")
        self._short.append(short)
        return self

    def long(self, long: str) -> 'Command':
        typecheck(long, str)
        long = long.strip()
        if not long.startswith("--"):
            raise ValueError(f"command {self.name()}: long-flag must start with '--'")
        self._long.append(long)
        return self

    def arg(self, arg: Union['Flag', 'Param']) -> 'Command':
        typecheck(arg, Union[Flag, Param])

        for flag in self._flags:
            if flag.name() == arg._name:
                raise ValueError(f"command {self._name}: item with name {arg._name!r} already exists")
        for param in self._params:
            if param.name() == arg._name:
                raise ValueError(f"command {self._name}: item with name {arg._name!r} already exists")

        if isinstance(arg, Flag):
            if len(arg.get_short()) + len(arg.get_long()) == 0:
                raise ValueError("flag must have at least on short/long name")
            self._flags.append(arg)
        else:
            if not arg.is_optional() and len(self._params) > 0 and self._params[-1].is_optional():
                raise ValueError(f"command {self.name()}: optional parameters must appear last")
            self._params.append(arg)
        return self

    def name(self) -> str:
        return self._name

    def description(self) -> Optional[str]:
        return self._description

    def get_short(self) -> List[str]:
        return self._short

    def get_long(self) -> List[str]:
        return self._long

    def disable_name(self) -> bool:
        return self._disable_name

    def flags(self) -> List['Flag']:
        return self._flags

    def params(self) -> List['Param']:
        return self._params


class Flag:
    _name: str
    _description: Optional[str]
    _required: bool
    _short: List[str]
    _long: List[str]
    _parser: Optional[Callable[[str], Any]]
    _kind: Literal["value", "count", "present"]
    _default: Any

    def __init__(self, name: str, description: Optional[str] = None):
        typecheck(name, str)
        typecheck(description, Optional[str])

        name = name.strip()
        if not name:
            raise ValueError("name must be a non-empty string!")

        self._name = name
        self._description = description
        self._required = False
        self._short = list()
        self._long = list()
        self._parser = None
        self._kind = "present"
        self._default = None

    def short(self, name: str) -> 'Flag':
        typecheck(name, str)
        name = name.strip()
        if name.startswith("--"):
            raise ValueError(f"command {self.name()}: short-flag cannot start with '--'")
        if not name.startswith("-"):
            raise ValueError(f"command {self.name()}: short-flag must start with '-'")
        if len(name) != 2:
            raise ValueError(f"command {self.name()}: short-flags must be only 2 characters long!")
        self._short.append(name)
        return self

    def long(self, name: str) -> 'Flag':
        typecheck(name, str)
        name = name.strip()
        if not name.startswith("--"):
            raise ValueError(f"command {self.name()}: long-flag must start with '--'")
        if len(name) == 2:
            raise ValueError(f"command {self.name()}: long-flag must not be empty")
        self._long.append(name)
        return self

    def optional(self) -> 'Flag':
        self._required = False
        return self

    def parser(self, parser: Callable[[str], Any]) -> 'Flag':
        typecheck(parser, Callable)
        if self._kind != "value":
            raise ValueError(f"flag {self._name}: only 'valued' flags can set a value-parser")
        self._parser = parser
        return self

    def valued(self) -> 'Flag':
        self._kind = "value"
        return self

    def count(self) -> 'Flag':
        self._kind = "count"
        return self

    def default(self, val) -> 'Flag':
        self._default = val
        return self

    def name(self) -> str:
        return self._name

    def description(self) -> Optional[str]:
        return self._description

    def is_optional(self) -> bool:
        return not self._required

    def is_required(self) -> bool:
        return self._required

    def get_short(self) -> List[str]:
        return self._short

    def get_long(self) -> List[str]:
        return self._long

    def kind(self) -> Literal["present", "value", "count"]:
        return self._kind

    def get_parser(self) -> Optional[Callable[[str], Any]]:
        return self._parser

    def get_default(self) -> Any:
        return self._default


class Param:
    _name: str
    _description: Optional[str]
    _required: bool
    _parser: Optional[Callable[[str], Any]]
    _default: Any

    def __init__(self, name: str, description: Optional[str] = None):
        typecheck(name, str)
        typecheck(description, Optional[str])

        name = name.strip()
        if not name:
            raise ValueError("name must be a non-empty string!")

        self._name = name
        self._description = description
        self._required = True
        self._parser = None
        self._default = None

    def optional(self) -> 'Param':
        self._required = False
        return self

    def parser(self, parser: Callable[[str], Any]) -> 'Param':
        typecheck(parser, Callable)
        self._parser = parser
        return self

    def default(self, val) -> 'Param':
        self._default = val
        return self

    def name(self) -> str:
        return self._name

    def description(self) -> Optional[str]:
        return self._description

    def is_optional(self) -> bool:
        return not self._required

    def get_parser(self) -> Optional[Callable[[str], Any]]:
        return self._parser

    def get_default(self) -> Any:
        return self._default


class Args:
    _command: str
    _values: SimpleNamespace

    def __init__(self, command: str, values: SimpleNamespace) -> None:
        typecheck(command, str)
        typecheck(values, SimpleNamespace)
        self._command = command
        self._values = values

    def command(self) -> str:
        return self._command

    def values(self) -> SimpleNamespace:
        return self._values

class _ArgParse:
    commands: List[Command]
    argv: List[str]
    command: Command
    idx: int
    param_idx: int
    values: SimpleNamespace
    required_flags: set[str]

    def _find_long_flag(self, val: str) -> Optional[Flag]:
        for flag in self.command.flags():
            for flag_long in flag.get_long():
                if val == flag_long:
                    return flag
        return None

    def _parse_long(
            self,
            arg_value: str,
    ):
        parts = arg_value.split("=", 1)
        flag_name = arg_value if len(parts) == 1 else parts[0]
        flag = self._find_long_flag(flag_name)
        if not flag:
            raise ValueError(f"{self.command.name()}: unknown flag --{flag_name}")

        # required-value tracking
        if flag.name() in self.required_flags:
            self.required_flags.remove(flag.name())

        # value-handling
        if len(parts) == 2 and flag.kind() != "value":
            raise ValueError(f"{self.command.name()}: flag --{flag_name} was provided a value but is not a valued-flag!")

        if flag.kind() == "value":
            if len(parts) != 2:
                if self.idx >= len(self.argv):
                    raise ValueError(f"{self.command.name()}: expected positional argument from flag '--{flag_name}'")
                value = self.argv[self.idx]
                self.idx += 1
            else:
                value = parts[1]
            parser = flag.get_parser()
            if parser:
                try:
                    value = parser(value)
                except (InterruptedError, KeyboardInterrupt) as err:
                    raise err
                except Exception as err:
                    raise ValueError(f"{self.command.name()}: invalid argument from flag '--{flag_name}' -- {err}")

            if hasattr(self.values, flag.name()):
                getattr(self.values, flag.name()).append(value)
            else:
                setattr(self.values, flag.name(), [value])
        elif flag.kind() == "count":
            count: int = getattr(self.values, flag.name(), 0) + 1
            setattr(self.values, flag.name(), count)
        elif flag.kind() == "present":
            if hasattr(self.values, flag.name()):
                raise ValueError(f"{self.command.name()}: flag '{flag.name()}' specified more than once")
            setattr(self.values, flag.name(), True)
        else:
            assert False, "unreachable"

    def _find_short_flag(self, flag_name: str) -> Optional[Flag]:
        for flag in self.command.flags():
            for short_flag in flag.get_short():
                if short_flag == flag_name:
                    return flag
        return None

    def _parse_short(self, arg_value: str):
        flag_names = list('-' + c for c in arg_value[1:])
        if len(flag_names) == 0:
            raise ValueError("invalid argument '-'")

        for flag_name in flag_names:
            flag = self._find_short_flag(flag_name)
            if not flag:
                raise ValueError(f"{self.command.name()}: unknown flag '-{flag_name}'")

            # required-value tracking
            if flag.name() in self.required_flags:
                self.required_flags.remove(flag.name())

            # value-handling
            if flag.kind() == "value":
                parser = flag.get_parser()
                if self.idx >= len(self.argv):
                    raise ValueError(f"{self.command.name()}: expected positional argument from flag '-{flag_name}'")
                value = self.argv[self.idx]
                self.idx += 1
                if parser:
                    try:
                        value = parser(value)
                    except (InterruptedError, KeyboardInterrupt) as err:
                        raise err
                    except Exception as err:
                        raise ValueError(f"{self.command.name()}: invalid argument from flag '-{flag_name}' -- {err}")
                if hasattr(self.values, flag.name()):
                    getattr(self.values, flag.name()).append(value)
                else:
                    setattr(self.values, flag.name(), [value])
            elif flag.kind() == "count":
                count: int = getattr(self.values, flag.name(), 0) + 1
                setattr(self.values, flag.name(), count)
            elif flag.kind() == "present":
                if hasattr(self.values, flag.name()):
                    raise ValueError(f"{self.command.name()}: flag '-{flag_name}' specified more than once")
                setattr(self.values, flag.name(), True)
            else:
                assert False, "unreachable"
    def _find_command(self, command_name: str) -> Optional[Command]:
        return _find_command(self.commands, command_name)


def _find_command(commands: List[Command], command_name: str) -> Optional[Command]:
    for command in commands:
        
        # check the command name
        if not command.disable_name() and command_name.lower() == command.name().lower():
            return command

        # check the short-flags
        for short in command.get_short():
            if short == command_name:
                return command

        # check the long-flags
        for long in command.get_long():
            if long == command_name:
                return command
    return None


def parse_args(commands: List[Command], argv: Optional[List[str]] = None) -> Args:
    if argv is None:
        import sys
        argv = sys.argv[1:]

    if len(argv) == 0:
        raise ValueError("no command specified")

    parser: _ArgParse = _ArgParse()
    parser.commands = commands
    parser.argv = argv

    command = parser._find_command(argv[0])
    if not command:
        raise ValueError(f"unknown command: {argv[0]!r}")
    parser.command = command
    parser.values = SimpleNamespace()
    parser.param_idx = 0
    parser.idx = 1
    parser.required_flags = set()
    for flag in command.flags():
        if flag.is_required():
            parser.required_flags.add(flag.name())

    while parser.idx < len(argv):
        arg_value = argv[parser.idx]
        parser.idx += 1

        if arg_value.startswith("--"):
            parser._parse_long(arg_value)
        elif arg_value.startswith("-"):
            parser._parse_short(arg_value)
        else:
            if parser.param_idx >= len(command.params()):
                raise ValueError(f"{command.name()}: unexpected argument {arg_value!r}")
            param = command.params()[parser.param_idx]
            parser.param_idx += 1

            value = arg_value
            value_parser = param.get_parser()
            if value_parser is not None:
                try:
                    value = value_parser(value)
                except (InterruptedError, KeyboardInterrupt) as err:
                    raise err
                except Exception as err:
                    raise ValueError(f"{command.name()}: invalid argument {arg_value!r} -- {err}")
            setattr(parser.values, param.name(), value)

    # required-value checking
    if parser.param_idx < len(command.params()) and not command.params()[parser.param_idx].is_optional():
        raise ValueError(f"missing required argument {command.params()[parser.param_idx].name()!r}")

    if len(parser.required_flags) > 0:
        raise ValueError(f"required flags are missing: {', '.join(repr(i) for i in parser.required_flags)}")
   
    # default-values
    for param in command.params():
        if param.is_optional():
            if not hasattr(parser.values, param.name()):
                setattr(parser.values, param.name(), param.get_default())
    for flag in command.flags():
        if flag.is_optional():
            if not hasattr(parser.values, flag.name()):
                setattr(parser.values, flag.name(), flag.get_default())


    out = Args(command.name(), parser.values)
    return out

def print_help(
    name: str,
    description: str,
    commands: List[Command],
    file=None,
    argv: Optional[List[str]] = None
):
    print(file=file)
    print(f"{name} - {description}", file=file)
    print(file=file)

    if argv is None:
        import sys
        argv = sys.argv[1:]

    command: Optional[Command] = None
    if len(argv) > 0:
        command = _find_command(commands, argv[0])
    if command is not None:
        usage_items = []
        for param in command.params():
            usage_items.append(f"<{param.name()}>"
                               if not param.is_optional()
                               else f"[{param.name()}]")
        for flag in command.flags():
            parts = []
            for short in flag.get_short():
                parts.append(short)
            for long in flag.get_long():
                parts.append(long)
            item = "|".join(parts)
            if flag.kind() == "value":
                item += " ..."
            if flag.is_optional():
                item = f"[{item}]"
            else:
                item = f"<{item}>"
            usage_items.append(item)

        print(f"Usage: {name} {argv[0]} {' '.join(usage_items)}", file=file)
        print(file=file)
        print(command.description(), file=file)
        print(file=file)
        print("Arguments:", file=file)
        items: list[str] = list()
        max_width = 0
        for param in command.params():
            if not param.is_optional():
                item = f"<{param.name()}>"
            else:
                item = f"[{param.name()}]"
            items.append(item)
            max_width = max(max_width, len(item))
        for item, param in zip(items, command.params()):
            default = param.get_default()
            if default:
                default = f"(default {default!r})"
            else:
                default = ""
            print(f"  {item:<{max_width}} {param.description() or ''} {default}", file=file)

        print(file=file)
        print("Flags:", file=file)
        flags: list[str] = list()
        max_width = 0
        for flag in command.flags():
            parts = []
            for short in flag.get_short():
                parts.append(short)
            for long in flag.get_long():
                parts.append(long)
            item = ", ".join(parts)
            if flag.is_optional():
                item = f"[{item}]"
            else:
                item = f"<{item}>"
            max_width = max(max_width, len(item))
            flags.append(item)
        for name, flag in zip(flags, command.flags()):
            default = flag.get_default()
            if default:
                default = "(default {default!r})"
            else:
                default = ""
            print(f"  {name:<{max_width}} {flag.description() or ''} {default}", file=file)
        else:
            default = ""
    else:
        print(f"Usage: {name} <command> [args...] [flags...]", file=file)
        print(file=file)
        print(f"Commands:", file=file)
        names = []
        max_width = 0
        for command in commands:
            parts: list[str] = []
            if not command.disable_name():
                parts.append(command.name())
            for short in command.get_short():
                parts.append(short)
            for long in command.get_long():
                parts.append(long)
            command_name: str = ", ".join(parts)
            max_width = max(max_width, len(command_name))
            names.append(command_name)
        for cmd_name, cmd in zip(names, commands):
            print(f"  {cmd_name:<{max_width}} {cmd.description() or ''}", file=file)
    print(file=file)

