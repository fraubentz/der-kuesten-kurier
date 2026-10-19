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
  const vb = $('vorlesen');  // Seite vorlesen mit der Stimme des Browsers
  if (!('speechSynthesis' in window)) { vb.hidden = true; } else {
    let aktiv = false;
    const stop = () => { speechSynthesis.cancel(); aktiv = false; vb.textContent = 'Vorlesen'; };
    vb.onclick = () => {
      if (aktiv) { stop(); return; }
      const zeilen = $('inhalt').innerText.split(/\n+/).map(s => s.trim()).filter(Boolean);
      const stimme = speechSynthesis.getVoices().find(v => v.lang && v.lang.toLowerCase().startsWith('de'));
      aktiv = true; vb.textContent = 'Vorlesen beenden';
      zeilen.forEach((z, i) => {
        const u = new SpeechSynthesisUtterance(z);
        u.lang = 'de-DE'; u.rate = 0.9; if (stimme) u.voice = stimme;
        if (i === zeilen.length - 1) u.onend = stop;
        speechSynthesis.speak(u);
      });
    };
    window.addEventListener('pagehide', () => speechSynthesis.cancel());
  }
})();
