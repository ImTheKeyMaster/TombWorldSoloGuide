from pathlib import Path
from versioning import CURRENT_APP_VERSION

ROOT=Path(__file__).resolve().parents[1]
APP=(ROOT/'app.js').read_text(encoding='utf-8')
CSS=(ROOT/'styles.css').read_text(encoding='utf-8')
INDEX=(ROOT/'index.html').read_text(encoding='utf-8')
WORKER=(ROOT/'service-worker.js').read_text(encoding='utf-8')
RECOVERY=APP.split('function renderStartupRecovery(error)',1)[1].split('if(startupInitializationError)',1)[0]

def test_versions_consistent():
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER
    assert f'V{CURRENT_APP_VERSION}' in INDEX

def test_recovery_shows_real_error_without_mutating_save():
    assert "String(error?.message||error||'Unknown startup error')" in RECOVERY
    assert 'escapeHtml(explanation)' in RECOVERY
    assert 'The Guide could not finish loading' in RECOVERY
    assert "const stored=localStorage.getItem" not in RECOVERY
    assert "stored=localStorage.getItem(STORAGE_KEY)" in RECOVERY
    assert "localStorage.setItem" not in RECOVERY
    assert "localStorage.removeItem" not in RECOVERY

def test_export_is_prominent_and_uses_safe_browser_download():
    assert 'class="btn secondary" id="exportStoredSave"' in RECOVERY
    assert 'document.body.appendChild(link)' in RECOVERY
    assert 'link.download=' in RECOVERY
    assert "setTimeout(()=>{link.remove();URL.revokeObjectURL(downloadUrl);},15000)" in RECOVERY
    assert "URL.revokeObjectURL(downloadUrl);link.click()" not in RECOVERY

def test_retry_does_not_reset_game():
    assert "$('#retryStartup').onclick=()=>window.location.reload()" in RECOVERY
    assert 'startup-recovery-error' in CSS
