const patterns = [
  ["operator", /^[=]/],
  ["parenthesis", /^[()]/],
  ["bracket", /^[\[\]]/],
  ["special", /^(?:[.,!\-]|:-|\?-)/],
  ["comment", /^%.*/],
  ["number", /^[0-9]|[1-9][0-9]+/],
  ["constant", /^(?:false|true)/],
  ["constant", /^[a-zA-Z][a-zA-Z_0-9]*/],
  ["identifier", /^[A-Z][a-zA-Z_0-9]*/],
  ["whitespace", /^\s+/],
];

function tokenize(source) {
  console.log(source);
  const lines = source.split(/\n/g);

  const processedLines = [];
  for (const line of lines) {
    const { bg, tokens } = tokenizeLine(line);
    processedLines.push({ bg, tokens });
  }
  console.log(processedLines);
  return processedLines;
}

function tokenizeLine(line) {
  if (line === "") {
    return { tokens: [] };
  }

  const tokens = [];
  while (line) {
    let matched = false;
    for (const [type, pattern] of patterns) {
      const match = line.match(pattern);
      console.log(match, line)
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
  return { tokens };
}

function makeHTML(lines) {
  return lines
    .map((line) => {
      const tokens = line.tokens
        .map((token) => {
          return `<span class="highlight-${token.type}">${token.value}</span>`;
        })
        .join("");
      return `<span class="line">${tokens}</span>`;
    })
    .join("<br />");
}

document.addEventListener("DOMContentLoaded", () => {
  [...document.querySelectorAll(".code.prolog pre code")].forEach((node) => {
    node.innerHTML = makeHTML(tokenize(node.textContent.trim()));
  });
});
