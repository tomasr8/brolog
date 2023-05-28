const keywords = [
  "False",
  "None",
  "True",
  "and",
  "as",
  "assert",
  "break",
  "case",
  "class",
  "continue",
  "def",
  "del",
  "elif",
  "else",
  "except",
  "finally",
  "for",
  "from",
  "global",
  "if",
  "import",
  "in",
  "is",
  "lambda",
  "match",
  "nonlocal",
  "not",
  "or",
  "pass",
  "raise",
  "return",
  "try",
  "while",
  "with",
  "yield",
];

const builtins = [
  "abs",
  "dict",
  "help",
  "min",
  "setattr",
  "all",
  "dir",
  "hex",
  "next",
  "slice",
  "any",
  "divmod",
  "id",
  "object",
  "sorted",
  "ascii",
  "enumerate",
  "input",
  "oct",
  "staticmethod",
  "bin",
  "eval",
  "int",
  "open",
  "str",
  "bool",
  "exec",
  "isinstance",
  "ord",
  "sum",
  "bytearray",
  "filter",
  "issubclass",
  "pow",
  "super",
  "bytes",
  "float",
  "iter",
  "print",
  "tuple",
  "callable",
  "format",
  "len",
  "property",
  "type",
  "chr",
  "frozenset",
  "list",
  "range",
  "vars",
  "classmethod",
  "getattr",
  "locals",
  "repr",
  "zip",
  "compile",
  "globals",
  "map",
  "reversed",
  "_import_",
  "complex",
  "hasattr",
  "max",
  "round",
  "delattr",
  "hash",
  "memoryview",
  "set",
];

const patterns = [
  ["keyword", new RegExp(`^(?:${keywords.join("|")})`)],
  ["constant", /^False|True/],
  ["string", /^('|"|'''|""").*?\1/],
  ["operator", /^[=+\-*/%&|<>!]/],
  ["parenthesis", /^[\[\](){}]/],
  ["special", /^[,:.]/],
  ["comment", /^#.*/],
  ["number", /^[0-9]|[1-9][0-9]+/],
  ["identifier", /^[a-zA-Z_][a-zA-Z_0-9]*/],
  ["whitespace", /^\s+/],
];

function tokenize(source) {
  console.log(source);
  const tokens = [];
  while (source) {
    let matched = false;
    for (const [type, pattern] of patterns) {
      const match = source.match(pattern);
      if (match) {
        tokens.push({ type, value: match[0] });
        source = source.slice(match[0].length);
        console.log(match);
        matched = true;
        break;
      }
    }
    if (!matched) {
      console.log("not mnatched");
      break;
    }
  }
  console.log(tokens);
  return tokens;
}

function postProcess(tokens) {
  const processed = [];

  let i = 0;
  while (i < tokens.length) {
    const first = tokens[i];
    const second = tokens[i + 1] || {};
    const third = tokens[i + 2] || {};

    if (
      first.type === "keyword" &&
      first.value === "class" &&
      third.type === "identifier"
    ) {
      processed.push(first);
      processed.push(second);
      processed.push({ type: "class-def", value: third.value });
      i += 3;
    } else if (
      first.type === "keyword" &&
      first.value === "def" &&
      third.type === "identifier"
    ) {
      processed.push(first);
      processed.push(second);
      processed.push({ type: "function-def", value: third.value });
      i += 3;
    } else {
      processed.push(first);
      i++;
    }
  }
  console.log(processed);
  return processed;
}

function makeHTML(tokens) {
  return tokens
    .map((token) => {
      return `<span class="highlight-${token.type}">${token.value}</span>`;
    })
    .join("");
}

document.addEventListener("DOMContentLoaded", () => {
  const source = `
  class Function(Term):
      """A function term, e.g., \`f(c)\`"""

      def __init__(self, name, args: list[Term]):
          self.name = name
          self.arity = len(args)
          self.args = args

      def __repr__(self):
          args = ', '.join([repr(arg) for arg in self.args])
          return f'{self.name}({args})'


  class Variable(Term):
      """A variable, e.g., \`X\` which takes on values of other terms"""

      def __init__(self, name):
          self.name = name

      def __repr__(self):
          short_id = str(id(self))[-2:]
          return f'{self.name}_{short_id}..'
      
      def __hash__(self):
          return id(self)
      
      def __eq__(self, other):
          return self is other


  def unify(x: Symbol | list[Term], y: Symbol | list[Term]):
      match (x, y):
          case (Atom(), Atom()) if x.name == y.name:
              return {}
          case (Function(), Function()) if x.name == y.name and x.arity == y.arity:
              return unify(x.args, y.args)
          case (Predicate(), Predicate()) if x.name == y.name and x.arity == y.arity:
              return unify(x.args, y.args)
          case (Variable(), Variable()):
              if x == y:
                  return {}
              else:
                  return {x: y}
          case (Variable(), (Atom() | Function()) as term):
              if not contains(term, x):
                  return {x: term}
          case ((Atom() | Function()) as term, Variable()):
              if not contains(term, y):
                  return {y: term}
          case (list(), list()) if len(x) == len(y):
              current = {}
              for a, b in zip(x, y):
                  a = substitute(a, current)
                  b = substitute(b, current)

                  if (new := unify(a, b)) is None:
                      return
                  current |= new
              return current
    `;
  document.getElementById("code").innerHTML = makeHTML(
    postProcess(tokenize(source))
  );
});
