function escapeHTML(str) {
  return str.replace(/[&<>"']/g, function (m) {
    return ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#39;'
    })[m];
  });
}

function formatDateLabel(dt){
  var d = new Date(dt.getFullYear(), dt.getMonth(), dt.getDate());
  var now = new Date();
  var today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  var diffMs = d.getTime() - today.getTime();
  var oneDay = 24*60*60*1000;
  if (diffMs === 0) return 'Today';
  if (diffMs === -oneDay) return 'Yesterday';
  var months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  return d.getDate() + ' ' + months[d.getMonth()] + ' ' + d.getFullYear();
}

function appendDateSeparatorIfNeeded(containerEl, dt){
  var dstr = dt.getFullYear()+'-'+('0'+(dt.getMonth()+1)).slice(-2)+'-'+('0'+dt.getDate()).slice(-2);
  var last = containerEl.getAttribute('data-last-date') || '';
  if (last !== dstr) {
    var sep = document.createElement('div');
    sep.className = 'date-sep';
    sep.textContent = formatDateLabel(dt);
    containerEl.appendChild(sep);
    containerEl.setAttribute('data-last-date', dstr);
  }
}

function getAvatarText(nameOrEmail){
  var s = (nameOrEmail || '').trim();
  if (!s) return '?';
  var m = s.match(/^[A-Za-z]/);
  if (m && m[0]) return m[0].toUpperCase();
  var m2 = s.match(/[A-Za-z]/);
  return m2 ? m2[0].toUpperCase() : s[0];
}

function renderMessage(containerEl, msg) {
  const sender = escapeHTML(msg.sender || 'System');
  const role = escapeHTML(msg.sender_role || '');
  const text = escapeHTML(msg.message || '');
  const dt = new Date(msg.created_at);
  const timeStr = dt.toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'});
  appendDateSeparatorIfNeeded(containerEl, dt);
  const row = document.createElement('div');
  var curName = containerEl.getAttribute('data-current-user-name') || '';
  var curEmail = containerEl.getAttribute('data-current-user-email') || '';
  var mine = sender === curName || sender === curEmail;
  row.className = mine ? 'msg-row right' : 'msg-row left';
  const bubble = document.createElement('div');
  bubble.className = mine ? 'msg msg-right' : 'msg msg-left';
  var nameLine = role ? (sender + ' - ' + role) : sender;
  bubble.innerHTML = '<div class="msg-header"><strong>' + nameLine + '</strong></div><p class="msg-text">' + text + '</p>';
  const avatar = document.createElement('div');
  avatar.className = 'avatar';
  avatar.textContent = getAvatarText(sender);
  if (mine) {
    row.appendChild(bubble);
    row.appendChild(avatar);
  } else {
    row.appendChild(avatar);
    row.appendChild(bubble);
  }
  containerEl.appendChild(row);
  const timeRow = document.createElement('div');
  timeRow.className = mine ? 'time-row right' : 'time-row left';
  timeRow.innerHTML = '<small>' + timeStr + '</small>';
  containerEl.appendChild(timeRow);
  containerEl.scrollTop = containerEl.scrollHeight;
}

function initStudentConversation(studentId) {
  const wsScheme = window.location.protocol === "https:" ? "wss" : "ws";
  var hostname = window.location.hostname;
  var port = window.location.port ? (':' + window.location.port) : '';
  var primaryHost = hostname + port;
  var fallbackHost = hostname + ':8000';
  var attemptedFallback = false;
  var httpMode = false;
  var socket = new WebSocket(wsScheme + '://' + primaryHost + '/ws/student/' + studentId + '/');
  const messagesEl = document.getElementById('messages-' + studentId);
  const formEl = document.getElementById('conv-form-' + studentId);
  const textarea = formEl ? formEl.querySelector('textarea[name="message"]') : null;

  function loadMessagesHTTP(){
    fetch('/students/conversation/' + studentId + '/messages/').then(function(r){ return r.json(); }).then(function(d){
      if (!messagesEl) return;
      messagesEl.innerHTML = '';
      messagesEl.setAttribute('data-last-date','');
      if (Array.isArray(d.messages)) {
        d.messages.forEach(function(m){ renderMessage(messagesEl, m); });
      }
    }).catch(function(){});
  }
  function sendMessageHTTP(text){
    var fd = new FormData();
    fd.append('message', text);
    fetch('/students/conversation/' + studentId + '/send/', { method: 'POST', body: fd }).then(function(r){ return r.json(); }).then(function(d){
      if (d && d.ok && d.message) {
        renderMessage(messagesEl, d.message);
      }
    }).catch(function(){});
  }

  socket.onerror = function(){
    try { console.warn('Conversation socket error - inline'); } catch(e){}
    if (!attemptedFallback && port && port !== ':8000') {
      attemptedFallback = true;
      try { socket.close(); } catch(e){}
      try {
        socket = new WebSocket(wsScheme + '://' + fallbackHost + '/ws/student/' + studentId + '/');
        attachInlineHandlers(socket, messagesEl, formEl, textarea);
      } catch(e){}
    } else {
      httpMode = true;
      loadMessagesHTTP();
    }
  };
  socket.onclose = function(){
    try { console.warn('Conversation socket closed - inline'); } catch(e){}
    if (!attemptedFallback && port && port !== ':8000') {
      attemptedFallback = true;
      try {
        socket = new WebSocket(wsScheme + '://' + fallbackHost + '/ws/student/' + studentId + '/');
        attachInlineHandlers(socket, messagesEl, formEl, textarea);
      } catch(e){}
    } else {
      httpMode = true;
      loadMessagesHTTP();
    }
  };
  socket.onmessage = function (e) {
    const data = JSON.parse(e.data);
    if (data.action === 'init' && Array.isArray(data.messages)) {
      messagesEl.innerHTML = '';
      messagesEl.setAttribute('data-last-date','');
      data.messages.forEach(function (m) { renderMessage(messagesEl, m); });
    } else if (data.action === 'new_message' && data.message) {
      renderMessage(messagesEl, data.message);
    }
  };

  if (formEl && textarea) {
    formEl.addEventListener('submit', function (ev) {
      ev.preventDefault();
      const text = textarea.value.trim();
      if (!text) return;
      if (!httpMode && socket && socket.readyState === 1) {
        try {
          socket.send(JSON.stringify({ action: 'send', message: text }));
          textarea.value = '';
        } catch (e) {}
      } else {
        sendMessageHTTP(text);
        textarea.value = '';
      }
    });
  }
  function attachInlineHandlers(sock, messagesEl, formEl, textarea){
    sock.onmessage = function (e) {
      const data = JSON.parse(e.data);
      if (data.action === 'init' && Array.isArray(data.messages)) {
        messagesEl.innerHTML = '';
        data.messages.forEach(function (m) { renderMessage(messagesEl, m); });
      } else if (data.action === 'new_message' && data.message) {
        renderMessage(messagesEl, data.message);
      }
    };
  }
}

var StudentConversationManager = (function(){
  var socket = null;
  var currentId = null;
  var modalInstance = null;
  var tableRowEl = null;
  function cleanup(){
    try { if (socket) { socket.close(); socket = null; } } catch(e){}
    try { document.body.classList.remove('modal-open'); } catch(e){}
    try { document.body.style.removeProperty('padding-right'); } catch(e){}
    try { document.body.style.removeProperty('overflow'); } catch(e){}
    try {
      var bds = document.querySelectorAll('.modal-backdrop');
      bds.forEach(function(b){ try { b.remove(); } catch(e){} });
    } catch(e){}
  }
  function updateRowCells(rowEl, msg){
    try {
      if (!rowEl || !msg) return;
      var feedbackCell = rowEl.querySelector('.cell-feedback');
      var updatedByCell = rowEl.querySelector('.cell-updated-by');
      var updatedAtCell = rowEl.querySelector('.cell-updated-at');
      var messageText = '';
      var updatedBy = '';
      var createdAt = '';
      if (typeof msg === 'object' && msg) {
        if (typeof msg.message === 'string') {
          messageText = msg.message.trim();
          updatedBy = msg.sender || '';
          createdAt = msg.created_at || '';
        } else if (typeof msg.feedback === 'string') {
          messageText = msg.feedback.trim();
          updatedBy = msg.updated_by_name || '';
          createdAt = msg.updated_at || '';
        }
      }
      if (feedbackCell) {
        feedbackCell.textContent = messageText || '—';
        if (messageText) {
          feedbackCell.setAttribute('title', messageText);
          try {
            var existing = bootstrap.Tooltip.getInstance(feedbackCell);
            if (existing) { existing.dispose(); }
            new bootstrap.Tooltip(feedbackCell);
          } catch(e){}
        } else {
          feedbackCell.removeAttribute('title');
        }
      }
      if (updatedByCell) {
        updatedByCell.textContent = (updatedBy || '—') || '—';
      }
      if (updatedAtCell) {
        try {
          var dt = createdAt ? new Date(createdAt) : new Date();
          var months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
          var dd = ('0' + dt.getDate()).slice(-2);
          var hh = ('0' + dt.getHours()).slice(-2);
          var mm = ('0' + dt.getMinutes()).slice(-2);
          updatedAtCell.textContent = dd + ' ' + months[dt.getMonth()] + ' ' + dt.getFullYear() + ', ' + hh + ':' + mm;
        } catch(e){
          updatedAtCell.textContent = '';
        }
      }
    } catch(e){}
  }
  function connect(id, messagesEl, formEl, textareaEl, titleEl, sname, scode, rowEl){
    if (socket) {
      try { socket.close(); } catch(e){}
      socket = null;
    }
    currentId = id;
    tableRowEl = rowEl || null;
    messagesEl.innerHTML = '';
    messagesEl.setAttribute('data-last-date','');
    var wsScheme = window.location.protocol === "https:" ? "wss" : "ws";
    var hostname = window.location.hostname;
    var port = window.location.port ? (':' + window.location.port) : '';
    var primaryHost = hostname + port;
    socket = new WebSocket(wsScheme + '://' + primaryHost + '/ws/student/' + id + '/');
    socket.onerror = function(){
      try { console.warn('Conversation socket error - modal'); } catch(e){}
    };
    socket.onclose = function(){
      try { console.warn('Conversation socket closed - modal'); } catch(e){}
    };
    socket.onmessage = function(e){
      var data = JSON.parse(e.data);
      if (data.action === 'init' && Array.isArray(data.messages)) {
        messagesEl.innerHTML = '';
        messagesEl.setAttribute('data-last-date','');
        data.messages.forEach(function(m){ renderMessage(messagesEl, m); });
      } else if (data.action === 'new_message' && data.message) {
        renderMessage(messagesEl, data.message);
        updateRowCells(tableRowEl, data.message);
      } else if (data.action === 'feedback_updated' && (data.feedback || data.updated_by_name)) {
        updateRowCells(tableRowEl, data);
      } else if (data.action === 'error') {
        try { console.warn('Conversation action error: ' + (data.reason || '')); } catch(e){}
      }
    };
    if (titleEl) {
      var titleText = '';
      if (sname && scode) {
        titleText = sname + ' - ' + scode;
      } else if (sname) {
        titleText = sname + ' - Student ' + id;
      } else {
        titleText = 'Student ' + id;
      }
      titleEl.textContent = titleText;
    }
    if (formEl && textareaEl) {
      var sendBtn = formEl.querySelector('#conv-modal-send');
      if (sendBtn) {
        sendBtn.onclick = function(){
          var text = textareaEl.value.trim();
          if (!text) return;
          if (socket && socket.readyState === 1) {
            try {
              socket.send(JSON.stringify({ action: 'send', message: text }));
              textareaEl.value = '';
            } catch(e){}
          }
        };
      }
      formEl.onsubmit = function(ev){ ev.preventDefault(); };
      textareaEl.addEventListener('keydown', function(ev){
        if (ev.key === 'Enter' && !ev.shiftKey) {
          ev.preventDefault();
          var text = textareaEl.value.trim();
          if (!text) return;
          if (socket && socket.readyState === 1) {
            try {
              socket.send(JSON.stringify({ action: 'send', message: text }));
              textareaEl.value = '';
            } catch(e){}
          }
        }
      });
    }
    function attachModalHandlers(sock, messagesEl){
      sock.onmessage = function(e){
        var data = JSON.parse(e.data);
        if (data.action === 'init' && Array.isArray(data.messages)) {
          messagesEl.innerHTML = '';
          messagesEl.setAttribute('data-last-date','');
          data.messages.forEach(function(m){ renderMessage(messagesEl, m); });
        } else if (data.action === 'new_message' && data.message) {
          renderMessage(messagesEl, data.message);
          updateRowCells(tableRowEl, data.message);
        } else if (data.action === 'feedback_updated' && (data.feedback || data.updated_by_name)) {
          updateRowCells(tableRowEl, data);
        } else if (data.action === 'error') {
          try { console.warn('Conversation action error: ' + (data.reason || '')); } catch(e){}
        }
      };
    }
  }
  function openModal(id, sname, scode, rowEl){
    var modalEl = document.getElementById('conversationModal');
    if (!modalEl) return;
    var messagesEl = document.getElementById('conv-modal-messages');
    var formEl = document.getElementById('conv-modal-form');
    var textareaEl = document.getElementById('conv-modal-textarea');
    var titleEl = document.getElementById('conv-modal-title');
    connect(id, messagesEl, formEl, textareaEl, titleEl, sname, scode, rowEl);
    if (modalInstance) {
      try { modalInstance.hide(); } catch(e){}
      modalInstance = null;
    }
    var modal = new bootstrap.Modal(modalEl, {backdrop: true, keyboard: true, focus: true});
    modalInstance = modal;
    if (!modalEl.getAttribute('data-cleanup-listener')) {
      modalEl.addEventListener('hidden.bs.modal', function(){ cleanup(); });
      modalEl.addEventListener('hide.bs.modal', function(){ setTimeout(cleanup, 10); });
      document.addEventListener('hidden.bs.modal', function(){ cleanup(); });
      document.addEventListener('hide.bs.modal', function(){ setTimeout(cleanup, 10); });
      var closeBtn = modalEl.querySelector('.btn-close');
      if (closeBtn) {
        closeBtn.addEventListener('click', function(){
          try {
            var inst = bootstrap.Modal.getInstance(modalEl) || modalInstance;
            if (inst) { inst.hide(); if (inst.dispose) inst.dispose(); }
          } catch(e){}
          setTimeout(cleanup, 30);
        });
      }
      modalEl.setAttribute('data-cleanup-listener', '1');
    }
    modal.show();
  }
  return {
    open: openModal
  };
})();
