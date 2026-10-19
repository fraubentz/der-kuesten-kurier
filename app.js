(() => {
  const root = document.documentElement;
  const $ = id => document.getElementById(id);
  const save = (k, v) => { try { localStorage.setItem(k, v); } catch {} };
  const load = k => { try { return localStorage.getItem(k); } catch { return null; } };

  // Sync year in colophon
  const yr = $('year');
  if (yr) yr.textContent = new Date().getFullYear();

  // Font size adjustment (A+ / A-)
  let size = parseFloat(load('size')) || 112.5;
  const setSize = s => {
    size = Math.min(160, Math.max(100, s));
    root.style.fontSize = size + '%';
    save('size', size);
  };
  setSize(size);

  const btnBigger = $('bigger');
  if (btnBigger) btnBigger.onclick = () => setSize(size + 12.5);

  const btnSmaller = $('smaller');
  if (btnSmaller) btnSmaller.onclick = () => setSize(size - 12.5);

  // High Contrast toggle
  const hc = $('contrast');
  if (hc) {
    const setHC = on => {
      root.classList.toggle('hc', on);
      hc.setAttribute('aria-pressed', on ? 'true' : 'false');
      save('hc', on ? '1' : '0');
    };
    hc.onclick = () => setHC(!root.classList.contains('hc'));
    setHC(load('hc') === '1');
  }
})();