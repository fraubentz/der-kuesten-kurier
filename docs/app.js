(() => {
  const root = document.documentElement, $ = id => document.getElementById(id);
  const save = (k, v) => { try { localStorage.setItem(k, v); } catch {} };
  const load = k => { try { return localStorage.getItem(k); } catch { return null; } };
  $('year').textContent = new Date().getFullYear();
  let size = parseFloat(load('size')) || 112.5;
  const setSize = s => { size = Math.min(160, Math.max(100, s)); root.style.fontSize = size + '%'; save('size', size); };
  setSize(size);
  $('bigger').onclick = () => setSize(size + 12.5);
  $('smaller').onclick = () => setSize(size - 12.5);
  const hc = $('contrast');
  const setHC = on => { root.classList.toggle('hc', on); hc.setAttribute('aria-pressed', on); save('hc', on ? 1 : 0); };
  hc.onclick = () => setHC(!root.classList.contains('hc'));
  setHC(load('hc') === '1');
})();
