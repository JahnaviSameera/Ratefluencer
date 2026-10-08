const fs = require('fs');
const content = fs.readFileSync('track2/frontend/sections.jsx', 'utf8');
let opens = 0, closes = 0;
for (let i = 0; i < content.length; i++) {
    if (content[i] === '{') opens++;
    else if (content[i] === '}') closes++;
}
console.log('{ count:', opens, '} count:', closes, 'diff:', opens - closes);
if (opens !== closes) console.log('UNCLOSED BRACES DETECTED');
else console.log('Braces balanced OK');

// Check for common crash patterns
const lines = content.split('\n');
lines.forEach((line, i) => {
    if (line.includes('style="') && !line.includes('style="{"')) {
        console.log('HTML style= at line', i+1, ':', line.trim().slice(0,80));
    }
});
