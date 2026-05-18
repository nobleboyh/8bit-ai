function escapeHtml(s: string): string {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
}

function isValidHex(colour: string): boolean {
  return /^#[0-9a-fA-F]{6}$/.test(colour)
}

export function buildAvatarHTML(grid: string[][], label: string, prefix: string, username: string): string {
  const n = grid.length
  if (n === 0) {
    return '<!DOCTYPE html>\n<html lang="en">\n<head>\n  <meta charset="UTF-8">\n  <meta name="viewport" content="width=device-width, initial-scale=1.0">\n  <title>Pixelforce Avatar</title>\n</head>\n<body>\n  <p>No avatar data</p>\n</body>\n</html>'
  }

  const cells = grid.map((row) => {
    if (row.length !== grid[0].length) {
      row.length = grid[0].length
    }
    return row.map((colour) => {
      const safeColour = isValidHex(colour) ? colour : '#000000'
      return `      <div style="background:${escapeHtml(safeColour)}"></div>`
    }).join('\n')
  }).join('\n')

  const escapedLabel = escapeHtml(label)

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${escapeHtml(prefix)} ${escapeHtml(username)} — Pixelforce Avatar</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      background: #f5e6c8;
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
      font-family: monospace, sans-serif;
    }
    .container {
      text-align: center;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(${n}, 1fr);
      width: ${n * 16}px;
      aspect-ratio: 1 / 1;
      margin: 0 auto;
    }
    .grid > div {
      width: 100%;
      aspect-ratio: 1 / 1;
    }
    .label {
      margin-top: 1rem;
      font-size: 1rem;
      color: #333;
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="grid">
${cells}
    </div>
    <div class="label">${escapedLabel}</div>
  </div>
</body>
</html>`
}
