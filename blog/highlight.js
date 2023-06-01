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
  ["keyword", new RegExp(`^(?:${keywords.join("|")})\\b`)],
  ["constant", /^(?:False|True)/],
  ["string", /^('''|""").*?\1/ms],
  ["string", /^('|").*?\1/],
  ["operator", /^[=+\-*/%&|<>!]/],
  ["parenthesis", /^[\[\](){}]/],
  ["special", /^[;,:.]/],
  ["comment", /^#.*/],
  ["number", /^(?:[0-9]|[1-9][0-9]+)/],
  ["identifier", /^[a-zA-Z_][a-zA-Z_0-9]*/],
  ["whitespace", /^\s+/],
];

function tokenize(source) {
  const lines = source.split(/\n/g);
  // console.log(lines);

  const processedLines = [];
  for (const line of lines) {
    const { bg, tokens } = tokenizeLine(line);
    processedLines.push({ bg, tokens });
  }
  // console.log(processedLines);
  return processedLines;
}

function tokenizeLine(line) {
  if (line === "") {
    return { tokens: [] };
  }
  // console.log(">>>>", line);
  let bg;
  if (line[0] === "+") {
    bg = "#42934245";
    line = line.slice(1);
  } else if (line[0] === "-") {
    bg = "rgba(229, 83, 75, 0.28)";
    line = line.slice(1);
  }

  const tokens = [];
  while (line) {
    let matched = false;
    for (const [type, pattern] of patterns) {
      const match = line.match(pattern);
      if (match) {
        tokens.push({ type, value: match[0] });
        line = line.slice(match[0].length);
        matched = true;
        break;
      }
    }
    if (!matched) {
      console.log("not mnatched");
      break;
    }
  }
  return { bg, tokens };
}

function postProcessLines(lines) {
  return lines.map(({ bg, tokens }) => {
    return { bg, tokens: postProcess(tokens) };
  });
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
  // console.log(processed);
  return processed;
}

function makeHTML(lines) {
  return lines
    .map((line) => {
      const bg = `background-color: ${line.bg};` || "";
      const tokens = line.tokens
        .map((token) => {
          return `<span class="highlight-${token.type}">${token.value}</span>`;
        })
        .join("");
      return `<span class="line" style="${bg}">${tokens}</span>`;
    })
    .join("<br />");
}

document.addEventListener("DOMContentLoaded", () => {
  [...document.querySelectorAll('.code:not(.prolog) pre code')].forEach(node => {
    node.innerHTML = makeHTML(postProcessLines(tokenize(node.textContent.trim())))
  })
});
