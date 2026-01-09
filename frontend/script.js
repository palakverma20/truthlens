// =======================
// THEME TOGGLE
// =======================
function initTheme() {
  const savedTheme = localStorage.getItem("theme") || "dark";
  document.documentElement.setAttribute("data-theme", savedTheme);
  document.body.setAttribute("data-theme", savedTheme);
}

function toggleTheme() {
  const currentTheme =
    document.body.getAttribute("data-theme") || "dark";
  const newTheme = currentTheme === "dark" ? "light" : "dark";

  document.documentElement.setAttribute("data-theme", newTheme);
  document.body.setAttribute("data-theme", newTheme);
  localStorage.setItem("theme", newTheme);
}

const themeToggle = document.getElementById("themeToggle");
if (themeToggle) {
  themeToggle.addEventListener("click", toggleTheme);
}

initTheme();

// =======================
// ELEMENT REFERENCES
// =======================
const messageInput = document.getElementById("messageInput");
const fileInput = document.getElementById("fileInput");
const charCount = document.getElementById("charCount");
const analyzeBtn = document.getElementById("analyzeBtn");
const loadingState = document.getElementById("loadingState");
const resultsSection = document.getElementById("resultsSection");
const errorState = document.getElementById("errorState");
const errorMessage = document.getElementById("errorMessage");

// =======================
// CHARACTER COUNTER
// =======================
messageInput.addEventListener("input", () => {
  charCount.textContent = messageInput.value.length;

  // Clear file if user starts typing
  if (fileInput && fileInput.value) {
    fileInput.value = "";
  }
});

fileInput?.addEventListener("change", () => {
  if (fileInput.files.length > 0) {
    messageInput.value = "";
    charCount.textContent = "0";
  }
});

// =======================
// ANALYZE BUTTON
// =======================
analyzeBtn.addEventListener("click", async () => {
  const text = messageInput.value.trim();
  const file = fileInput?.files[0];

  if (!text && !file) {
    showError("Please enter text or upload a file to analyze.");
    return;
  }

  analyzeBtn.disabled = true;
  showLoading();
  hideError();
  hideResults();
  hideError();

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 35000);

    let response;

    if (file) {
  const allowedTypes = [
    "text/plain",
    "application/pdf",
    "image/png",
    "image/jpeg"
  ];

  if (!allowedTypes.includes(file.type)) {
    showError("Unsupported file type. Please upload PDF, TXT, or Image.");
    hideLoading();
    analyzeBtn.disabled = false;
    return;
  }
}



    // =======================
    // CASE 1: FILE UPLOAD
    // =======================
    if (file) {
      const formData = new FormData();
      formData.append("file", file);

      response = await fetch(
        "https://truthlens-backend-dgxw.onrender.com/analyze",
        {
          method: "POST",
          body: formData,
          signal: controller.signal,
        }
      );
    }

    // =======================
    // CASE 2: TEXT INPUT
    // =======================
    else {
      if (text.length > 5000) {
        showError("Message exceeds 5000 character limit.");
        hideLoading();
        analyzeBtn.disabled = false;
        return;
      }

      response = await fetch(
        "https://truthlens-backend-dgxw.onrender.com/analyze",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text }),
          signal: controller.signal,
        }
      );
    }

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || "Analysis failed");
    }

    const data = await response.json();
    displayResults(data);
    hideLoading();
  } catch (error) {
    console.error("Error:", error);
    if (error.name === "AbortError") {
      showError("Request took too long. Please try again.");
    } else {
      showError("Error analyzing input: " + error.message);
    }
    hideLoading();
  } finally {
    analyzeBtn.disabled = false;
  }
});

// =======================
// UI HELPERS
// =======================

function showLoading() {
  loadingState.classList.remove("hidden");
}

function hideLoading() {
  loadingState.classList.add("hidden");
}

function hideResults() {
  resultsSection.classList.add("hidden");
}

function showError(message) {
  errorMessage.textContent = message;
  errorState.classList.remove("hidden");
}

function hideError() {
  errorState.classList.add("hidden");
}

// =======================
// DISPLAY RESULTS
// =======================
function displayResults(data) {
  const score = data.score || 0;

  const truncateText = (text, maxLength = 200) =>
    text.length > maxLength
      ? text.substring(0, maxLength) + "..."
      : text;

  document.getElementById("explanationText").textContent =
    data.explanation;
  document.getElementById("emotionText").textContent = truncateText(
    data.emotion
  );
  document.getElementById("logicText").textContent = truncateText(
    data.logic
  );
  document.getElementById("patternText").textContent = truncateText(
    data.pattern
  );

  const riskFill = document.getElementById("riskFill");
  const riskScore = document.getElementById("riskScore");
  const riskDescription = document.getElementById("riskDescription");

  riskFill.style.width = "0%";
  riskScore.textContent = "0";
  void riskFill.offsetWidth;

  riskFill.style.width = score + "%";
  riskScore.textContent = score;

  let riskLevel = "Low Risk";
  let riskColor = "var(--accent-green)";
  if (score > 60) {
    riskLevel = "High Risk";
    riskColor = "var(--accent-red)";
  } else if (score > 30) {
    riskLevel = "Medium Risk";
    riskColor = "var(--accent-cyan)";
  }

  riskDescription.textContent = riskLevel;
  riskScore.style.color = riskColor;

  if (data.mood) {
    const moodBadge = document.getElementById("moodBadge");
    document.getElementById("moodEmoji").textContent = data.mood.emoji;
    document.getElementById("moodLabel").textContent = data.mood.label;
    moodBadge.className = "mood-badge " + data.mood.class;
    moodBadge.classList.remove("hidden");
  }

  resultsSection.classList.remove("hidden");
}

