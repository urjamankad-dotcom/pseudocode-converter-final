// ── Constants ──
const PASSCODE = "LJU2025";
const FREE_LIMIT = 3;
const UPI_ID = "YOUR_UPI_ID@upi"; // Replace with your actual UPI ID
const UPI_NAME = "PseudoCode Converter";
const UPI_AMOUNT = "99";

// ── Example Pseudocodes ──
const EXAMPLES = {
  bubble: `FUNCTION bubbleSort(arr, n)
  FOR i FROM 0 TO n-1
    FOR j FROM 0 TO n-i-2
      IF arr[j] > arr[j+1] THEN
        SWAP arr[j] AND arr[j+1]
      END IF
    END FOR
  END FOR
  RETURN arr
END FUNCTION`,

  binary: `FUNCTION binarySearch(arr, target, low, high)
  WHILE low <= high
    mid = (low + high) / 2
    IF arr[mid] == target THEN
      RETURN mid
    ELSE IF arr[mid] < target THEN
      low = mid + 1
    ELSE
      high = mid - 1
    END IF
  END WHILE
  RETURN -1
END FUNCTION`,

  factorial: `FUNCTION factorial(n)
  IF n == 0 OR n == 1 THEN
    RETURN 1
  END IF
  RETURN n * factorial(n - 1)
END FUNCTION`,

  fibonacci: `FUNCTION fibonacci(n)
  SET a = 0
  SET b = 1
  FOR i FROM 0 TO n-1
    PRINT a
    SET temp = a + b
    SET a = b
    SET b = temp
  END FOR
END FUNCTION`
};

// ── State ──
function getUsageCount() {
  if (localStorage.getItem("pc_unlocked") === "true") return 0;
  return parseInt(localStorage.getItem("pc_count") || "0");
}

function incrementUsage() {
  const count = getUsageCount() + 1;
  localStorage.setItem("pc_count", count.toString());
  return count;
}

function isUnlocked() {
  return localStorage.getItem("pc_unlocked") === "true";
}

function unlockApp() {
  localStorage.setItem("pc_unlocked", "true");
}

// ── UI Helpers ──
function showError(msg) {
  const el = document.getElementById("errorBanner");
  el.textContent = msg;
  el.style.display = "block";
  setTimeout(() => { el.style.display = "none"; }, 5000);
}

function hideError() {
  document.getElementById("errorBanner").style.display = "none";
}

function setLoading(isLoading) {
  const btn = document.getElementById("convertBtn");
  const text = btn.querySelector(".btn-text");
  const loader = btn.querySelector(".btn-loader");
  btn.disabled = isLoading;
  text.style.display = isLoading ? "none" : "inline";
  loader.style.display = isLoading ? "flex" : "none";
}

function updateUsageNote() {
  const note = document.getElementById("usageNote");
  if (isUnlocked()) {
    note.textContent = "✅ Unlimited access unlocked";
    note.style.color = "var(--success)";
    return;
  }
  const used = getUsageCount();
  const remaining = FREE_LIMIT - used;
  if (remaining > 0) {
    note.textContent = `${remaining} free conversion${remaining === 1 ? "" : "s"} remaining`;
  } else {
    note.textContent = "Free conversions used — ₹99 to unlock unlimited";
    note.style.color = "var(--error)";
  }
}

// ── Paywall ──
function showPaywall() {
  const upiLink = `upi://pay?pa=${encodeURIComponent(UPI_ID)}&pn=${encodeURIComponent(UPI_NAME)}&am=${UPI_AMOUNT}&cu=INR`;
  document.getElementById("upiBtn").href = upiLink;
  document.getElementById("paywallModal").style.display = "flex";
}

function verifyPasscode() {
  const input = document.getElementById("passcodeInput").value.trim();
  const errorEl = document.getElementById("unlockError");
  if (input === PASSCODE) {
    unlockApp();
    document.getElementById("paywallModal").style.display = "none";
    updateUsageNote();
    showError(""); // clear any errors
    handleConvert(); // auto-convert after unlock
  } else {
    errorEl.style.display = "block";
    setTimeout(() => { errorEl.style.display = "none"; }, 3000);
  }
}

// ── Example Pills ──
document.querySelectorAll(".example-pill").forEach(btn => {
  btn.addEventListener("click", () => {
    const key = btn.dataset.example;
    const textarea = document.getElementById("pseudoInput");
    textarea.value = EXAMPLES[key];
    updateCharCount();
    handleConvert();
  });
});

// ── Char Count ──
function updateCharCount() {
  const textarea = document.getElementById("pseudoInput");
  const count = textarea.value.length;
  const el = document.getElementById("charCount");
  el.textContent = `${count} / 2000`;
  el.style.color = count > 1800 ? "var(--error)" : "var(--muted)";
}

document.getElementById("pseudoInput").addEventListener("input", updateCharCount);

// ── Main Convert Handler ──
async function handleConvert() {
  hideError();
  const pseudocode = document.getElementById("pseudoInput").value.trim();

  if (!pseudocode) {
    showError("Please enter some pseudocode first.");
    return;
  }

  if (pseudocode.length > 2000) {
    showError("Input too long — please keep pseudocode under 2000 characters.");
    return;
  }

  // Freemium check
  if (!isUnlocked() && getUsageCount() >= FREE_LIMIT) {
    showPaywall();
    return;
  }

  setLoading(true);

  try {
    const response = await fetch("/convert", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pseudocode })
    });

    const data = await response.json();

    if (!response.ok || data.error) {
      showError(data.error || "Conversion failed. Please try again.");
      return;
    }

    // Increment usage after successful conversion
    if (!isUnlocked()) incrementUsage();
    updateUsageNote();

    renderOutput(data);

  } catch (err) {
    showError("Network error. Please check your connection and try again.");
  } finally {
    setLoading(false);
  }
}

// ── Render Output ──
function renderOutput(data) {
  // Show the grid
  const grid = document.getElementById("outputGrid");
  grid.style.display = "grid";

  // Populate code blocks
  ["python", "java", "cpp"].forEach(lang => {
    const codeEl = document.getElementById(`code-${lang}`);
    codeEl.textContent = data[lang] || "";
  });

  // Re-run Prism highlighting
  Prism.highlightAll();

  // Populate commentary
  const body = document.getElementById("commentaryBody");
  body.innerHTML = "";

  if (data.commentary && Array.isArray(data.commentary)) {
    data.commentary.forEach(item => {
      const row = document.createElement("div");
      row.className = "commentary-row";
      row.innerHTML = `
        <span class="commentary-linenum">${item.line}</span>
        <span class="commentary-pseudo">${escapeHtml(item.pseudo)}</span>
        <span class="commentary-explain">${escapeHtml(item.explanation)}</span>
      `;
      body.appendChild(row);
    });
  }

  // Scroll to output
  grid.scrollIntoView({ behavior: "smooth", block: "start" });
}

// ── Copy Code ──
function copyCode(lang) {
  const code = document.getElementById(`code-${lang}`).textContent;
  navigator.clipboard.writeText(code).then(() => {
    const btns = document.querySelectorAll(`#card-${lang} .copy-btn`);
    btns.forEach(btn => {
      btn.textContent = "Copied!";
      btn.classList.add("copied");
      setTimeout(() => {
        btn.textContent = "Copy";
        btn.classList.remove("copied");
      }, 2000);
    });
  });
}

// ── Utility ──
function escapeHtml(str) {
  const div = document.createElement("div");
  div.appendChild(document.createTextNode(str));
  return div.innerHTML;
}

// ── Init ──
updateUsageNote();
