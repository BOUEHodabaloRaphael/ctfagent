// kBxAc dynamic challenge panel (team_dynamic type).
//
// Interface mirrors CTFd/plugins/challenges/assets/view.js: the challenge
// loader calls CTFd._internal.challenge.postRender after rendering the
// modal, and submit() behaves exactly like the standard one (the server in
// challenge.py remains authoritative; this file is UX only).
//
// No secrets, flags, job IDs, or backend URLs ever touch this file. All
// DOM text from the server uses text-only insertion.

CTFd._internal.challenge.data = undefined;

CTFd._internal.challenge.preRender = function() {};

var KbxacDynamic = (function() {
  // Status is re-checked shortly after a non-terminal answer so finished
  // files appear promptly; each poll is a single cheap indexed read and the
  // timer always stops on terminal states, modal close, or repeated errors.
  var POLL_MS = 3000;
  // Short DOM-settle retry: postRender can run before the theme injects the
  // challenge view HTML (first modal open). Re-checking the DOM is cheap
  // (no network) and recovers silently; the normal API interval below is
  // used for everything else.
  var DOM_RETRY_MS = 500;
  var MAX_CONSECUTIVE_FAILURES = 12;

  var timerId = null;
  var activeChallengeId = null;
  var failures = 0;
  var modalHooked = false;

  // script_root-aware API base: CTFd serves sub-path installs with
  // request.script_root exposed as CTFd.config.urlRoot; bare /plugins/…
  // URLs 404 there. urlRoot is "" on root installs, so this is a no-op
  // by default.
  var API_ROOT =
    (window.CTFd && CTFd.config && CTFd.config.urlRoot) || "";

  function challengeId() {
    var el = document.getElementById("challenge-id");
    return el ? parseInt(el.value, 10) : NaN;
  }

  function currentRequestedId() {
    // The challenge this modal open actually requested. The theme sets its
    // challenge store synchronously before postRender, while the modal DOM
    // still shows the previous challenge (or nothing on first open) — so
    // the DOM value is racily stale and must not be trusted blindly here.
    // Falls back to the DOM for themes without the Alpine store.
    try {
      if (window.Alpine && Alpine.store) {
        var store = Alpine.store("challenge");
        var sid = store && store.data && store.data.id;
        var n = parseInt(sid, 10);
        if (!isNaN(n)) return n;
      }
    } catch (e) {}
    return challengeId();
  }

  function setSubmitEnabled(enabled) {
    var input = document.getElementById("challenge-input");
    var button = document.getElementById("challenge-submit");
    if (input) input.disabled = !enabled;
    if (button) button.disabled = !enabled;
  }

  function clearTimer() {
    if (timerId !== null) {
      clearTimeout(timerId);
      timerId = null;
    }
  }

  function hookModalHide() {
    if (modalHooked) return;
    modalHooked = true;
    document.addEventListener("hidden.bs.modal", function(event) {
      if (event.target && event.target.id === "challenge-window") {
        clearTimer();
        activeChallengeId = null;
      }
    });
  }

  function panel() {
    var el = document.getElementById("kbxac-dynamic-panel");
    if (el) return el;
    // No anchor yet (view HTML not injected): return null so render() defers
    // instead of drawing into a detached node. The retry flow re-renders
    // once the challenge DOM exists.
    var parent = null;
    var before = null;
    var anchor = document.querySelector(".challenge-files");
    if (anchor && anchor.parentNode) {
      parent = anchor.parentNode;
      before = anchor;
    } else {
      var desc = document.querySelector(".challenge-desc");
      if (desc && desc.parentNode) {
        parent = desc.parentNode;
        before = desc.nextSibling;
      }
    }
    if (!parent) return null;
    el = document.createElement("div");
    el.id = "kbxac-dynamic-panel";
    el.className = "row pb-3";
    parent.insertBefore(el, before);
    return el;
  }

  function render(state, requestId) {
    // The file row mirrors a normal challenge attachment: while the file is
    // not available only a subtle spinner is shown (no status wording), and
    // once ready only the file link itself is shown. All identity (filename
    // label excluded) derives from the validated request, never from mutable
    // global state, so a late response cannot paint another challenge.
    var box = panel();
    if (!box) return;
    while (box.firstChild) box.removeChild(box.firstChild);
    var wrap = document.createElement("div");
    wrap.className = "col-12";

    if (state.status === "ready") {
      var a = document.createElement("a");
      a.className = "btn btn-info btn-file mb-1 d-inline-block px-2";
      a.href =
        API_ROOT +
        "/plugins/challenge_generator/api/download?challenge_id=" +
        encodeURIComponent(requestId);
      a.textContent = state.filename;
      wrap.appendChild(a);
      setSubmitEnabled(true);
    } else if (state.status === "generating") {
      var spin = document.createElement("i");
      spin.className = "fas fa-circle-notch fa-spin fa-fw";
      spin.setAttribute("role", "status");
      var label = document.createElement("span");
      label.className = "sr-only";
      label.textContent = "Loading challenge file";
      wrap.appendChild(spin);
      wrap.appendChild(label);
      setSubmitEnabled(false);
    } else if (state.status === "failed") {
      var p = document.createElement("p");
      p.className = "mb-2";
      p.textContent = state.message || "Challenge file unavailable.";
      wrap.appendChild(p);
      setSubmitEnabled(false);
    } else {
      // disabled / unavailable
      var q = document.createElement("p");
      q.className = "mb-2";
      q.textContent = state.message || "Challenge files are not available at the moment.";
      wrap.appendChild(q);
      setSubmitEnabled(false);
    }
    box.appendChild(wrap);
  }

  function terminal(status) {
    return (
      status === "ready" ||
      status === "failed" ||
      status === "disabled" ||
      status === "unavailable"
    );
  }

  function poll() {
    clearTimer();
    // Modal closed: stop permanently (hookModalHide sets null on hide).
    if (activeChallengeId === null) return;
    // Challenge DOM/store not settled yet (first modal open races the theme):
    // re-read the requested id and retry shortly instead of stopping forever.
    if (isNaN(activeChallengeId)) {
      activeChallengeId = currentRequestedId();
      if (isNaN(activeChallengeId)) {
        timerId = setTimeout(poll, DOM_RETRY_MS);
        return;
      }
      // Bound now: fall through to the normal fetch below.
    }
    // Re-validate against the live request source: a previous challenge's
    // DOM can linger, so never keep a stale binding.
    var live = currentRequestedId();
    if (!isNaN(live)) activeChallengeId = live;
    // Immutable identity for this request cycle. Responses are only applied
    // when it still matches the active challenge (see below).
    var requestId = activeChallengeId;
    var url =
      API_ROOT +
      "/plugins/challenge_generator/api/status?challenge_id=" +
      encodeURIComponent(requestId);
    fetch(url, { credentials: "same-origin" })
      .then(function(response) {
        if (response.status === 401) {
          if (requestId !== activeChallengeId) return null;
          render({ status: "failed", message: "Session expired — refresh the page." }, requestId);
          return null;
        }
        if (!response.ok) throw new Error("status " + response.status);
        return response.json();
      })
      .then(function(state) {
        if (!state) return;
        // Stale response (another challenge opened while this fetch was in
        // flight): discard entirely — no render, no terminal transition, no
        // timer changes. The current challenge owns its own lifecycle.
        if (requestId !== activeChallengeId) return;
        failures = 0;
        render(state, requestId);
        if (!terminal(state.status)) {
          timerId = setTimeout(poll, POLL_MS);
        }
      })
      .catch(function() {
        failures += 1;
        if (failures >= MAX_CONSECUTIVE_FAILURES) {
          if (requestId !== activeChallengeId) return;
          render({ status: "failed", message: "Status unavailable — try reopening." }, requestId);
          return;
        }
        timerId = setTimeout(poll, POLL_MS);
      });
  }

  function init() {
    hookModalHide();
    clearTimer();
    failures = 0;
    // Bind the requested challenge, not whatever the DOM happens to hold:
    // on cross-challenge opens the old modal DOM (previous id) is still
    // present until the theme swaps it.
    activeChallengeId = currentRequestedId();
    setSubmitEnabled(false);
    poll();
  }

  return { init: init, _pollIntervalMs: POLL_MS };
})();

CTFd._internal.challenge.postRender = function() {
  KbxacDynamic.init();
};

CTFd._internal.challenge.submit = function(preview) {
  var challenge_id = parseInt(CTFd.lib.$("#challenge-id").val());
  var submission = CTFd.lib.$("#challenge-input").val();

  var body = {
    challenge_id: challenge_id,
    submission: submission
  };
  var params = {};
  if (preview) {
    params["preview"] = true;
  }

  return CTFd.api.post_challenge_attempt(params, body).then(function(response) {
    if (response.status === 429) {
      return response;
    }
    if (response.status === 403) {
      return response;
    }
    return response;
  });
};

