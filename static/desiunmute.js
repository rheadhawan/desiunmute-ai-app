// DesiUnmute's small bits of JavaScript.
// Most of the site uses HTMX instead. JavaScript is only needed for things
// HTMX can't do: slowing down audio, recording from the microphone, and
// keeping track of a conversation.


// SLOW AUDIO
// The "Slow" button plays the Hindi audio at 70% speed.
// This listens on the whole page, so it also works on buttons added later.

document.addEventListener("click", function (event) {
  const button = event.target.closest(".slow-toggle");
  if (!button) return;

  const audio = button.closest(".player").querySelector("audio");
  const isSlow = audio.playbackRate < 1;

  audio.playbackRate = isSlow ? 1 : 0.7;
  button.classList.toggle("is-on", !isSlow);
  audio.currentTime = 0;
  audio.play();
});


// SENDING TO THE SERVER
// The "HX-Request" header tells the server to answer like it does for HTMX,
// so if the invite code has expired we can send the learner to the invite page.

async function sendForm(url, form) {
  const response = await fetch(url, {
    method: "POST",
    body: form,
    headers: { "HX-Request": "true" },
  });

  if (response.headers.get("HX-Redirect")) {
    window.location = response.headers.get("HX-Redirect");
    return null;
  }
  return response;
}

const CONNECTION_ERROR =
  '<div class="card error-box" role="alert"><p>We couldn\'t reach DesiUnmute. Check your internet and try again.</p></div>';


// RECORDER
// Turns a button into a record/stop button. When a recording finishes,
// it calls onRecorded(recording, fileName).

const MAX_SECONDS = 15;

function makeRecorder(button, status, labels, onRecorded) {
  let recorder = null;
  let chunks = [];
  let stopTimer = null;

  button.addEventListener("click", async function () {
    // 1. Already recording? Then this click means stop.
    if (recorder && recorder.state === "recording") {
      recorder.stop();
      return;
    }

    // 2. Ask for the microphone
    let stream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (error) {
      status.textContent =
        "We couldn't use your microphone. Click the icon next to the web address, allow the microphone, then reload the page.";
      return;
    }

    chunks = [];
    recorder = new MediaRecorder(stream);

    recorder.addEventListener("dataavailable", function (event) {
      chunks.push(event.data);
    });

    // 3. When it stops, turn the mic off and hand over the recording
    recorder.addEventListener("stop", function () {
      clearTimeout(stopTimer);
      stream.getTracks().forEach(function (track) { track.stop(); });

      button.textContent = labels.again;
      button.classList.remove("is-recording");

      const recording = new Blob(chunks, { type: recorder.mimeType });
      // Chrome makes .webm files and Safari makes .mp4 files
      const fileName = recording.type.includes("mp4") ? "recording.mp4" : "recording.webm";
      onRecorded(recording, fileName);
    });

    recorder.start();
    button.textContent = "■ Stop";
    button.classList.add("is-recording");
    status.textContent = labels.recording;
    stopTimer = setTimeout(function () { recorder.stop(); }, MAX_SECONDS * 1000);
  });
}


// PRONUNCIATION COACH PAGE

const recordButton = document.getElementById("record-button");

if (recordButton) {
  const recordStatus = document.getElementById("record-status");
  const myRecording = document.getElementById("my-recording");
  const myAudio = document.getElementById("my-audio");
  const feedbackButton = document.getElementById("feedback-button");
  const feedbackLoading = document.getElementById("feedback-loading");
  const result = document.getElementById("result");

  let lastRecording = null;
  let lastFileName = null;

  makeRecorder(
    recordButton,
    recordStatus,
    { again: "● Record again", recording: "Recording… say the phrase now." },
    function (recording, fileName) {
      lastRecording = recording;
      lastFileName = fileName;
      myAudio.src = URL.createObjectURL(recording);
      myRecording.hidden = false;
      feedbackButton.disabled = false;
      recordStatus.textContent = "Listen back if you like, then click Get feedback.";
    }
  );

  feedbackButton.addEventListener("click", async function () {
    if (!lastRecording) return;

    const form = new FormData();
    form.append("target_phrase", document.getElementById("target_phrase").value);
    form.append("recording", lastRecording, lastFileName);

    feedbackButton.disabled = true;
    feedbackLoading.style.display = "block";

    try {
      const response = await sendForm("/pronunciation/feedback", form);
      if (response) {
        result.innerHTML = await response.text();
        result.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    } catch (error) {
      result.innerHTML = CONNECTION_ERROR;
    }

    feedbackButton.disabled = false;
    feedbackLoading.style.display = "none";
  });
}


// CONVERSATION PAGE

const chat = document.getElementById("chat");

if (chat) {
  const slug = chat.dataset.slug;
  const chatLog = document.getElementById("chat-log");
  const chatEmpty = document.getElementById("chat-empty");
  const chatLoading = document.getElementById("chat-loading");
  const startButton = document.getElementById("start-button");
  const chatControls = document.getElementById("chat-controls");
  const talkButton = document.getElementById("talk-button");
  const talkStatus = document.getElementById("talk-status");
  const endButton = document.getElementById("end-button");
  const summaryLoading = document.getElementById("summary-loading");
  const summary = document.getElementById("summary");

  // The conversation so far, sent back with every turn so the AI remembers it
  let history = [];

  // Sends a request and adds the new chat bubbles
  async function takeTurn(url, form, waitingText) {
    chatLoading.textContent = waitingText;
    chatLoading.style.display = "block";
    talkButton.disabled = true;

    try {
      const response = await sendForm(url, form);
      if (response) {
        const data = await response.json();
        chatLog.insertAdjacentHTML("beforeend", data.html);
        if (data.history) history = data.history;   // errors don't change the history

        // Play the newest reply
        const players = chatLog.querySelectorAll(".bubble.character audio");
        if (players.length) players[players.length - 1].play().catch(function () {});

        chatLog.lastElementChild.scrollIntoView({ behavior: "smooth", block: "end" });
      }
    } catch (error) {
      chatLog.insertAdjacentHTML("beforeend", CONNECTION_ERROR);
    }

    chatLoading.style.display = "none";
    talkButton.disabled = false;
  }

  // 1. START: the character speaks first
  startButton.addEventListener("click", async function () {
    startButton.hidden = true;
    chatEmpty.remove();
    await takeTurn(`/conversation/${slug}/start`, new FormData(), "Calling…");

    if (history.length) {
      chatControls.hidden = false;
    } else {
      startButton.hidden = false;   // something went wrong, let them try again
    }
  });

  // 2. ANSWER OUT LOUD: sends as soon as they click Stop
  makeRecorder(
    talkButton,
    talkStatus,
    { again: "● Answer out loud", recording: "Listening… click Stop when you're done." },
    function (recording, fileName) {
      talkStatus.textContent = "Click, say your answer in Hindi, then click Stop. It sends by itself.";

      const form = new FormData();
      form.append("history", JSON.stringify(history));
      form.append("recording", recording, fileName);
      takeTurn(`/conversation/${slug}/reply`, form, "Listening to you…");
    }
  );

  // 3. END: summary of how it went
  endButton.addEventListener("click", async function () {
    const form = new FormData();
    form.append("history", JSON.stringify(history));

    endButton.disabled = true;
    summaryLoading.style.display = "block";

    try {
      const response = await sendForm(`/conversation/${slug}/summary`, form);
      if (response) summary.innerHTML = await response.text();
    } catch (error) {
      summary.innerHTML = CONNECTION_ERROR;
    }

    endButton.disabled = false;
    summaryLoading.style.display = "none";
  });
}
