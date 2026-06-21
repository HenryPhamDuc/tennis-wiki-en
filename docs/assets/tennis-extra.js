// Tennis WIKI - Client-side enhancements
// Add copy buttons to all preformatted code blocks
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('pre code').forEach((block) => {
        const btn = document.createElement('button');
        btn.className = 'copy-button';
        btn.textContent = '📋';
        btn.title = 'Copy to clipboard';
        btn.onclick = () => {
            navigator.clipboard.writeText(block.textContent);
            btn.textContent = '✓';
            setTimeout(() => btn.textContent = '📋', 1500);
        };
        block.parentElement.style.position = 'relative';
        block.parentElement.appendChild(btn);
    });
});
