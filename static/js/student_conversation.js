// Context Menu Logic
(function(){
  var menuId = 'chat-context-menu';
  var menu = document.getElementById(menuId);
  if (!menu) {
    menu = document.createElement('div');
    menu.id = menuId;
    menu.style.position = 'absolute';
    menu.style.display = 'none';
    menu.style.zIndex = '9999';
    menu.style.backgroundColor = '#fff';
    menu.style.border = '1px solid #ccc';
    menu.style.borderRadius = '4px';
    menu.style.boxShadow = '0 2px 5px rgba(0,0,0,0.2)';
    menu.style.minWidth = '120px';
    document.body.appendChild(menu);
    
    // Global click to close menu
    document.addEventListener('click', function(){
      menu.style.display = 'none';
    });
  }

  window.showContextMenu = function(e, msg, mine) {
    e.preventDefault();
    menu.innerHTML = '';
    var list = document.createElement('ul');
    list.style.listStyle = 'none';
    list.style.margin = '0';
    list.style.padding = '5px 0';
    
    // Info Option (Read Receipts)
    var infoItem = document.createElement('li');
    infoItem.style.padding = '6px 12px';
    infoItem.style.cursor = 'pointer';
    infoItem.style.fontSize = '14px';
    infoItem.innerHTML = '<i class="fas fa-info-circle me-2"></i> Info';
    infoItem.onmouseover = function(){ this.style.backgroundColor = '#f3f4f6'; };
    infoItem.onmouseout = function(){ this.style.backgroundColor = 'transparent'; };
    infoItem.onclick = function() {
      showMsgInfo(msg);
    };
    list.appendChild(infoItem);

    // Edit Option (Only if mine and text)
    if (mine && msg.type !== 'file') {
      var editItem = document.createElement('li');
      editItem.style.padding = '6px 12px';
      editItem.style.cursor = 'pointer';
      editItem.style.fontSize = '14px';
      editItem.innerHTML = '<i class="fas fa-pencil-alt me-2"></i> Edit Message';
      editItem.onmouseover = function(){ this.style.backgroundColor = '#f3f4f6'; };
      editItem.onmouseout = function(){ this.style.backgroundColor = 'transparent'; };
      editItem.onclick = function() {
        startEditing(msg.id);
      };
      list.appendChild(editItem);
    }

    menu.appendChild(list);
    
    // Position menu
    var x = e.pageX;
    var y = e.pageY;
    
    // Boundary checks (basic)
    if (x + 150 > window.innerWidth) x -= 150;
    
    menu.style.left = x + 'px';
    menu.style.top = y + 'px';
    menu.style.display = 'block';
  };
})();

function showMsgInfo(msg) {
  var modalId = 'msg-info-modal';
  var modal = document.getElementById(modalId);
  if (modal) modal.remove();
  
  var curName = document.body.getAttribute('data-current-name') || '';
  var curEmail = document.body.getAttribute('data-current-email') || '';

  // Build Read List
  var readListHtml = '<p class="text-muted small p-2 m-0">No read receipts yet.</p>';
  if (msg.read_by && msg.read_by.length > 0) {
    var others = msg.read_by.filter(function(r){ 
        return r.user !== curName && r.user !== curEmail; 
    });
    
    if (others.length > 0) {
        readListHtml = '<ul class="list-group list-group-flush">';
        others.forEach(function(r){
          var t = new Date(r.read_at);
          var timeStr = t.toLocaleDateString() + ' ' + t.toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'});
          readListHtml += '<li class="list-group-item d-flex justify-content-between align-items-center small">' +
            '<span>' + escapeHTML(r.user) + '</span>' +
            '<span class="text-muted" style="font-size:0.8em">' + timeStr + '</span>' +
            '</li>';
        });
        readListHtml += '</ul>';
    }
  }

  var modalHtml = 
    '<div class="modal fade" id="' + modalId + '" tabindex="-1" style="z-index: 10000;">' +
      '<div class="modal-dialog modal-dialog-centered modal-sm">' +
        '<div class="modal-content">' +
          '<div class="modal-header">' +
            '<h6 class="modal-title">Message Info</h6>' +
            '<button type="button" class="btn-close" data-bs-dismiss="modal"></button>' +
          '</div>' +
          '<div class="modal-body p-0">' +
             readListHtml +
          '</div>' +
        '</div>' +
      '</div>' +
    '</div>';
    
  document.body.insertAdjacentHTML('beforeend', modalHtml);
  var modalEl = document.getElementById(modalId);
  var bsModal = new bootstrap.Modal(modalEl);
  bsModal.show();
  modalEl.addEventListener('hidden.bs.modal', function(){
    modalEl.remove();
  });
}

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


window.resetMsgInputs = function(prefix) {
  // 1. Clear Hidden Inputs
  var tagInput = document.getElementById(prefix + '-hashtag-val');
  var prInput = document.getElementById(prefix + '-priority-val');
  if (tagInput) tagInput.value = '';
  if (prInput) prInput.value = '';

  // 2. Reset Buttons
  var hBtn = document.getElementById(prefix + 'HashtagBtn');
  var pBtn = document.getElementById(prefix + 'PriorityBtn');
  if (hBtn) hBtn.classList.remove('text-primary');
  if (pBtn) pBtn.classList.remove('text-primary');

  // 3. Reset Badges
  var hBadge = document.getElementById(prefix + '-hashtag-badge');
  var pBadge = document.getElementById(prefix + '-priority-badge');
  if (hBadge) { hBadge.innerHTML = ''; hBadge.className = 'ms-1 align-self-center'; }
  if (pBadge) { pBadge.innerHTML = ''; pBadge.className = 'ms-1 align-self-center'; }

  // 4. Clear Active State in Dropdowns
  if (hBtn && hBtn.nextElementSibling) {
      hBtn.nextElementSibling.querySelectorAll('.dropdown-item').forEach(function(item){
          item.classList.remove('active');
      });
  }
  if (pBtn && pBtn.nextElementSibling) {
      pBtn.nextElementSibling.querySelectorAll('.dropdown-item').forEach(function(item){
          item.classList.remove('active');
      });
  }
};

window.selectHashtag = function(val, mode) {
  var idPrefix = mode === 'remarks' ? 'remarks-' : 'conv-modal-';
  var btnId = mode === 'remarks' ? 'remarksHashtagBtn' : 'convModalHashtagBtn';
  var badgeId = idPrefix + 'hashtag-badge';
  var inputEl = document.getElementById(idPrefix + 'hashtag-val');
  var btnEl = document.getElementById(btnId);
  var badgeEl = document.getElementById(badgeId);
  
  if (!inputEl) return;
  
  var currentVal = inputEl.value ? inputEl.value.split(',') : [];
  
  if (val === '') {
      currentVal = [];
  } else {
      var index = currentVal.indexOf(val);
      if (index > -1) {
          currentVal.splice(index, 1);
      } else {
          currentVal.push(val);
      }
  }
  
  var newVal = currentVal.join(',');
  inputEl.value = newVal;

  if (btnEl) {
    if (currentVal.length > 0) btnEl.classList.add('text-primary');
    else btnEl.classList.remove('text-primary');
    
    // Update active state in dropdown
    var dropdownMenu = btnEl.nextElementSibling;
    if (dropdownMenu) {
        var items = dropdownMenu.querySelectorAll('.dropdown-item');
        items.forEach(function(item) {
            var onclick = item.getAttribute('onclick');
            if (onclick) {
                var match = onclick.match(/selectHashtag\('([^']+)'/);
                if (match && match[1]) {
                    var itemVal = match[1];
                    if (itemVal) {
                        if (currentVal.includes(itemVal)) item.classList.add('active');
                        else item.classList.remove('active');
                    } else if (val === '') {
                        // Clear all active if None selected
                         item.classList.remove('active');
                    }
                }
            }
        });
    }
  }
  if (badgeEl) {
    if (currentVal.length === 0) {
      badgeEl.innerHTML = '';
      badgeEl.className = 'ms-1 align-self-center';
    } else {
      badgeEl.innerHTML = '';
      badgeEl.className = 'ms-1 align-self-center';
      
      currentVal.forEach(function(tag) {
          var span = document.createElement('span');
          var badgeClass = 'badge rounded-pill me-1 ';
          var text = tag;
          if (tag === 'placement') {
            badgeClass += 'bg-primary';
            text = 'Placement';
          } else if (tag === 'class') {
            badgeClass += 'bg-info text-dark';
            text = 'Class';
          } else if (tag === 'payment') {
            badgeClass += 'bg-success';
            text = 'Payment';
          } else if (tag === 'followups') {
            badgeClass += 'bg-secondary';
            text = 'Followups';
          } else if (tag === 'important') {
            badgeClass += 'bg-danger';
            text = 'Important';
          } else {
            badgeClass += 'bg-secondary';
          }
          span.className = badgeClass;
          span.textContent = '#' + text;
          badgeEl.appendChild(span);
      });
    }
  }
};

window.selectPriority = function(val, mode) {
  var idPrefix = mode === 'remarks' ? 'remarks-' : 'conv-modal-';
  var btnId = mode === 'remarks' ? 'remarksPriorityBtn' : 'convModalPriorityBtn';
  var badgeId = idPrefix + 'priority-badge';
  var inputEl = document.getElementById(idPrefix + 'priority-val');
  var btnEl = document.getElementById(btnId);
  var badgeEl = document.getElementById(badgeId);

  if (inputEl) inputEl.value = val;
  if (btnEl) {
    if (val) btnEl.classList.add('text-primary');
    else btnEl.classList.remove('text-primary');
  }
  if (badgeEl) {
    if (!val) {
      badgeEl.innerHTML = '';
      badgeEl.className = 'ms-1 align-self-center';
    } else {
      var badgeClass = 'badge rounded-pill ';
      var text = val;
      if (val === 'high') {
        badgeClass += 'bg-danger';
        text = 'High';
      } else if (val === 'medium') {
        badgeClass += 'bg-warning text-dark';
        text = 'Medium';
      } else if (val === 'low') {
        badgeClass += 'bg-success';
        text = 'Low';
      } else {
        badgeClass += 'bg-secondary';
      }
      badgeEl.className = 'ms-1 align-self-center ' + badgeClass;
      badgeEl.textContent = '!' + text;
    }
  }
};

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

function formatFileSize(bytes) {
  if (typeof bytes !== 'number') return '';
  if (bytes < 1024) return bytes + ' B';
  else if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  else return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

window.revealImage = function(btn, url, msgId) {
  try {
    var wrapper = btn.closest('.chat-media-wrapper');
    if (!wrapper) return;
    var img = wrapper.querySelector('.chat-image-content');
    if (img) {
      img.src = url;
      img.style.display = 'block';
    }
    var overlay = wrapper.querySelector('.chat-media-blur-overlay');
    if (overlay) overlay.style.display = 'none';
    if (msgId) {
      localStorage.setItem('img_downloaded_' + msgId, 'true');
    }
  } catch(e){ console.error(e); }
};

window.startEditing = function(msgId) {
  var msgTextEl = document.getElementById('msg-text-' + msgId);
  if (!msgTextEl) return;
  
  var currentText = msgTextEl.getAttribute('data-raw-text') || msgTextEl.innerText;
  
  // Find student ID from container
  var container = msgTextEl.closest('[data-student-id]');
  var sid = container ? container.getAttribute('data-student-id') : null;

  // Create edit container
  var editContainer = document.createElement('div');
  editContainer.className = 'edit-container mt-2';
  editContainer.id = 'edit-container-' + msgId;
  
  var textarea = document.createElement('textarea');
  textarea.className = 'form-control mb-2';
  textarea.value = msgTextEl.innerText; 
  textarea.rows = 2;
  
  var btnGroup = document.createElement('div');
  btnGroup.className = 'd-flex justify-content-end gap-2';
  
  var cancelBtn = document.createElement('button');
  cancelBtn.className = 'btn btn-sm btn-secondary';
  cancelBtn.textContent = 'Cancel';
  cancelBtn.onclick = function() { cancelEdit(msgId); };
  
  var saveBtn = document.createElement('button');
  saveBtn.className = 'btn btn-sm btn-primary';
  saveBtn.textContent = 'Save';
  saveBtn.onclick = function() { saveEdit(msgId, textarea.value, sid); };
  
  btnGroup.appendChild(cancelBtn);
  btnGroup.appendChild(saveBtn);
  
  editContainer.appendChild(textarea);
  editContainer.appendChild(btnGroup);
  
  // Hide original text, show edit container
  msgTextEl.style.display = 'none';
  msgTextEl.parentNode.insertBefore(editContainer, msgTextEl.nextSibling);
};

window.cancelEdit = function(msgId) {
  var msgTextEl = document.getElementById('msg-text-' + msgId);
  var editContainer = document.getElementById('edit-container-' + msgId);
  if (msgTextEl) msgTextEl.style.display = 'block';
  if (editContainer) editContainer.remove();
};

window.saveEdit = function(msgId, newText, studentId) {
  document.dispatchEvent(new CustomEvent('conversation:edit_message', { 
    detail: { messageId: msgId, newText: newText, studentId: studentId } 
  }));
};

function renderMessage(containerEl, msg) {
  const sender = escapeHTML(msg.sender || 'System');
  const role = escapeHTML(msg.sender_role || '');
  const text = escapeHTML(msg.message || '');
  const hashtag = escapeHTML(msg.hashtag || '');
  const priority = escapeHTML(msg.priority || '');
  const dt = new Date(msg.created_at);
  const timeStr = dt.toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'});
  appendDateSeparatorIfNeeded(containerEl, dt);
  const row = document.createElement('div');
  row.id = 'msg-row-' + msg.id;
  var curName = containerEl.getAttribute('data-current-user-name') || document.body.getAttribute('data-current-name') || '';
  var curEmail = containerEl.getAttribute('data-current-user-email') || document.body.getAttribute('data-current-email') || '';
  var mine = sender === curName || sender === curEmail;
  row.className = mine ? 'msg-row right' : 'msg-row left';
  const bubble = document.createElement('div');
  bubble.className = mine ? 'msg msg-right' : 'msg msg-left';
  var nameLine = role ? (sender + ' - ' + role) : sender;
  var metaHtml = '';
  var tags = [];
  if (hashtag) tags.push('#' + hashtag);
  if (priority) tags.push('#' + priority);
  
  if (tags.length > 0) {
    var tagStyle = mine 
      ? 'font-size:0.85em; color: #e0e7ff; opacity: 0.9;' 
      : 'font-size:0.85em; color: #4b5563; font-weight: 600;';
    metaHtml = '<div class="mb-1" style="' + tagStyle + '">' + tags.join(' ') + '</div>';
  }
  
  var contentHtml = '';
  if (msg.type === 'file' && msg.file_url) {
    var fileUrl = msg.file_url;
    var fileName = escapeHTML(msg.file_name || 'File');
    var fileMime = msg.file_mime || '';
    var fileSize = msg.file_size || 0;
    
    if (fileMime.indexOf('image/') === 0) {
      var isDownloaded = false;
      if (msg.id) {
        isDownloaded = localStorage.getItem('img_downloaded_' + msg.id) === 'true';
      }
      
      // If it's my message or already downloaded, show image directly
      if (mine || isDownloaded) {
        contentHtml = '<div class="mb-2"><a href="' + fileUrl + '" target="_blank"><img src="' + fileUrl + '" alt="' + fileName + '" style="max-width: 200px; max-height: 200px; border-radius: 4px;" class="img-fluid"></a></div>';
      } else {
        var sizeStr = formatFileSize(fileSize);
        contentHtml = '<div class="mb-2 chat-media-wrapper">' +
           '<div class="chat-media-blur-overlay" onclick="revealImage(this, \'' + fileUrl + '\', ' + (msg.id || 'null') + ')">' +
             '<button class="chat-download-btn"><i class="fas fa-download"></i> ' + sizeStr + '</button>' +
           '</div>' +
           '<img src="" data-src="' + fileUrl + '" alt="' + fileName + '" class="chat-image-content" style="display:none; max-width: 200px; max-height: 200px; border-radius: 4px;">' +
           '</div>';
      }
    } else {
      contentHtml = '<div class="mb-2 p-2 bg-light border rounded"><a href="' + fileUrl + '" target="_blank" class="text-decoration-none text-dark d-flex align-items-center"><i class="fas fa-file me-2 text-primary"></i> <span class="text-truncate" style="max-width: 200px;">' + fileName + '</span> <i class="fas fa-download ms-auto text-muted"></i></a></div>';
    }
    if (text) {
      contentHtml += '<p class="msg-text mt-1" id="msg-text-' + msg.id + '">' + text + '</p>';
    }
  } else {
    contentHtml = '<p class="msg-text" id="msg-text-' + msg.id + '">' + text + '</p>';
  }

  // Edited indicator
  if (msg.is_edited) {
    contentHtml += '<div class="text-end" style="line-height:1;"><small style="font-size: 0.7rem; opacity: 0.8;">(edited)</small></div>';
  }

  bubble.innerHTML = '<div class="msg-header"><strong>' + nameLine + '</strong></div>' + metaHtml + contentHtml;
  
  // Context Menu Trigger
  bubble.addEventListener('contextmenu', function(e) {
      showContextMenu(e, msg, mine);
  });

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
  
  // Read receipts (visual only, detail in context menu)
  var extrasHtml = '';
  if (mine) {
      // Edit button REMOVED (now in context menu)
      
      // Read receipts
      if (msg.read_by && msg.read_by.length > 0) {
          // Filter out myself
          var others = msg.read_by.filter(function(r){ 
              return r.user !== curName && r.user !== curEmail; 
          });
          if (others.length > 0) {
              extrasHtml += '<span class="ms-2 text-primary"><i class="fas fa-check-double" style="font-size: 0.8rem;"></i></span>';
          } else {
              extrasHtml += '<span class="ms-2 text-muted"><i class="fas fa-check" style="font-size: 0.8rem;"></i></span>';
          }
      } else {
          extrasHtml += '<span class="ms-2 text-muted"><i class="fas fa-check" style="font-size: 0.8rem;"></i></span>';
      }
  } else {
      // Mark read logic for received messages
       if (msg.id) {
           // Only mark as read if we are in the active chat window for this student
           // We can check this by seeing if the container is visible or matches current student
           // But since this script is running, we assume we are processing messages for the active view.
           // However, if we have multiple lists/chats, we need to be careful.
           // For now, we assume renderMessage is called only for the active chat or during init.
           
           if (!window.pendingReadMarks) window.pendingReadMarks = new Map();
           var sid = containerEl.getAttribute('data-student-id');
           window.pendingReadMarks.set(msg.id, sid);
           
           clearTimeout(window.readMarkTimeout);
           window.readMarkTimeout = setTimeout(function(){
             var byStudent = {};
             window.pendingReadMarks.forEach(function(sId, mId){
                 if (!sId) return;
                 if (!byStudent[sId]) byStudent[sId] = [];
                 byStudent[sId].push(mId);
             });
             window.pendingReadMarks.clear();
             
             for (var sId in byStudent) {
                 document.dispatchEvent(new CustomEvent('conversation:mark_read', { 
                     detail: { messageIds: byStudent[sId], studentId: sId } 
                 }));
             }
           }, 1000);
       }
   }
 
   timeRow.innerHTML = '<small>' + timeStr + extrasHtml + '</small>';
  containerEl.appendChild(timeRow);
  containerEl.scrollTop = containerEl.scrollHeight;
}

function updateMessageUI(containerEl, msg) {
    var row = document.getElementById('msg-row-' + msg.id);
    if (row) {
        var temp = document.createElement('div');
        temp.setAttribute('data-current-user-name', containerEl.getAttribute('data-current-user-name'));
        temp.setAttribute('data-current-user-email', containerEl.getAttribute('data-current-user-email'));
        temp.setAttribute('data-student-id', containerEl.getAttribute('data-student-id'));
        
        renderMessage(temp, msg);
        var newRow = temp.firstElementChild;
        var newTimeRow = temp.lastElementChild;
        
        var next = row.nextSibling;
        containerEl.replaceChild(newRow, row);
        if (next && next.classList.contains('time-row')) {
            containerEl.replaceChild(newTimeRow, next);
        }
    }
}

function updateReadStatusUI(containerEl, msgIds, readBy) {
    msgIds.forEach(function(mid){
        var row = document.getElementById('msg-row-' + mid);
        if (row) {
            var timeRow = row.nextSibling;
            if (timeRow && timeRow.classList.contains('time-row')) {
                var icon = timeRow.querySelector('.fa-check');
                if (icon) {
                    icon.classList.remove('fa-check');
                    icon.classList.add('fa-check-double');
                    icon.parentElement.classList.remove('text-muted');
                    icon.parentElement.classList.add('text-primary');
                    
                    // No longer updating title tooltip as we use context menu for details
                    // But we could still update it if we wanted to support both
                }
            }
        }
    });
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
  if (messagesEl) {
    messagesEl.setAttribute('data-student-id', studentId);
  }
  const formEl = document.getElementById('conv-form-' + studentId);
  const textarea = formEl ? formEl.querySelector('textarea[name="message"]') : null;

  function loadMessagesHTTP(){
    fetch('/students/conversation/' + studentId + '/messages/')
    .then(function(r){ 
        if (!r.ok) { throw new Error(r.statusText); }
        return r.json(); 
    })
    .then(function(d){
      if (!messagesEl) return;
      messagesEl.innerHTML = '';
      messagesEl.setAttribute('data-last-date','');
      if (Array.isArray(d.messages)) {
        d.messages.forEach(function(m){ renderMessage(messagesEl, m); });
      }
    }).catch(function(e){ console.error(e); });
  }
  function sendMessageHTTP(text){
    var fd = new FormData();
    fd.append('message', text);
    var tagVal = '';
    var prVal = '';
    var tInput = document.getElementById('conv-modal-hashtag-val');
    var pInput = document.getElementById('conv-modal-priority-val');
    if (tInput) tagVal = tInput.value;
    if (pInput) prVal = pInput.value;
    if (tagVal) { fd.append('hashtag', tagVal); }
    if (prVal) { fd.append('priority', prVal); }
    fetch('/students/conversation/' + studentId + '/send/', { method: 'POST', body: fd }).then(function(r){ return r.json(); }).then(function(d){
        if (d && d.ok && d.message) {
          renderMessage(messagesEl, d.message);
          window.resetMsgInputs('conv-modal');
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
          var tagVal = '';
          var prVal = '';
          var tInput = document.getElementById('conv-modal-hashtag-val');
          var pInput = document.getElementById('conv-modal-priority-val');
          if (tInput) tagVal = tInput.value;
          if (pInput) prVal = pInput.value;
          
          var payload = { action: 'send', message: text };
          if (tagVal) payload.hashtag = tagVal;
          if (prVal) payload.priority = prVal;
          
          socket.send(JSON.stringify(payload));
          textarea.value = '';
          window.resetMsgInputs('conv-modal');
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
    if (messagesEl) messagesEl.setAttribute('data-student-id', id);
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
      } else if (data.action === 'message_updated' && data.message) {
        if (window.updateMessageBubble) {
           window.updateMessageBubble(data.message);
        }
        updateRowCells(tableRowEl, data.message);
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
              var tagVal = document.getElementById('conv-modal-hashtag-val').value;
              var prVal = document.getElementById('conv-modal-priority-val').value;
              var payload = { action: 'send', message: text };
              if (tagVal) { payload.hashtag = tagVal; }
              if (prVal) { payload.priority = prVal; }
              socket.send(JSON.stringify(payload));
              textareaEl.value = '';
              window.resetMsgInputs('conv-modal');
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
              var tagVal = document.getElementById('conv-modal-hashtag-val').value;
              var prVal = document.getElementById('conv-modal-priority-val').value;
              var payload = { action: 'send', message: text };
              if (tagVal) { payload.hashtag = tagVal; }
              if (prVal) { payload.priority = prVal; }
              socket.send(JSON.stringify(payload));
              textareaEl.value = '';
              window.resetMsgInputs('conv-modal');
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
    
    // Connect WebSocket
    connect(id, messagesEl, formEl, textareaEl, titleEl, sname, scode, rowEl);
    
    // Get or create modal instance
    var modal = bootstrap.Modal.getOrCreateInstance(modalEl, {backdrop: true, keyboard: true, focus: true});
    modalInstance = modal;
    
    // Attach cleanup listener only once
    if (!modalEl.getAttribute('data-cleanup-listener')) {
      modalEl.addEventListener('hidden.bs.modal', function(){ 
        cleanup(); 
      });
      modalEl.setAttribute('data-cleanup-listener', '1');
    }
    
    modal.show();
  }

  // Listen for edit message events (Global for modal)
  document.addEventListener('conversation:edit_message', function(e){
    if (!socket || socket.readyState !== 1) return;
    var d = e.detail;
    // Ensure we are sending to the correct student socket
    if (d.studentId && currentId && String(d.studentId) !== String(currentId)) return;
    
    try {
       socket.send(JSON.stringify({
         action: 'edit_message',
         message_id: d.messageId,
         new_text: d.newText
       }));
     } catch(err){ console.error(err); }
  });

  // Listen for mark read events (Global for modal)
  document.addEventListener('conversation:mark_read', function(e){
    if (!socket || socket.readyState !== 1) return;
    var d = e.detail;
    if (d.studentId && currentId && String(d.studentId) !== String(currentId)) return;
    
    try {
      socket.send(JSON.stringify({
        action: 'mark_read',
        message_ids: d.messageIds
      }));
    } catch(err){ console.error(err); }
  });

  return {
    open: openModal
  };
})();

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

window.selectPreviewHashtag = function(val, prefix) {
  var labelEl = document.getElementById(prefix + '-preview-hashtag-label');
  var inputEl = document.getElementById(prefix + '-preview-hashtag-val');
  var btnEl = document.getElementById(prefix + 'PreviewHashtagBtn');
  
  if (!inputEl) return;
  
  var currentVal = inputEl.value ? inputEl.value.split(',') : [];
  
  if (val === '') {
      currentVal = [];
  } else {
      var index = currentVal.indexOf(val);
      if (index > -1) {
          currentVal.splice(index, 1);
      } else {
          currentVal.push(val);
      }
  }
  
  var newVal = currentVal.join(',');
  inputEl.value = newVal;

  if (labelEl) {
      if (currentVal.length === 0) labelEl.textContent = 'Tag';
      else if (currentVal.length === 1) {
          var v = currentVal[0];
          if (v === 'placement') labelEl.textContent = 'Placement';
          else if (v === 'class') labelEl.textContent = 'Class';
          else if (v === 'payment') labelEl.textContent = 'Payment';
          else if (v === 'followups') labelEl.textContent = 'Followups';
          else if (v === 'important') labelEl.textContent = 'Important';
          else labelEl.textContent = v;
      } else {
          labelEl.textContent = currentVal.length + ' Tags';
      }
  }
  if (btnEl) {
      if (currentVal.length > 0) btnEl.classList.add('text-primary');
      else btnEl.classList.remove('text-primary');
      
      // Update active classes in dropdown
      var dropdownMenu = btnEl.nextElementSibling;
      if (dropdownMenu) {
          var items = dropdownMenu.querySelectorAll('.dropdown-item');
          items.forEach(function(item) {
              var onclick = item.getAttribute('onclick');
              if (onclick) {
                  var match = onclick.match(/selectPreviewHashtag\('([^']+)'/);
                  if (match && match[1]) {
                      var itemVal = match[1];
                      if (itemVal) {
                          if (currentVal.includes(itemVal)) item.classList.add('active');
                          else item.classList.remove('active');
                      }
                  }
              }
          });
      }
  }
};

window.selectPreviewPriority = function(val, prefix) {
  var labelEl = document.getElementById(prefix + '-preview-priority-label');
  var inputEl = document.getElementById(prefix + '-preview-priority-val');
  var btnEl = document.getElementById(prefix + 'PreviewPriorityBtn');
  if (inputEl) inputEl.value = val;
  if (labelEl) {
      if (!val) labelEl.textContent = 'Priority';
      else if (val === 'high') labelEl.textContent = 'High';
      else if (val === 'medium') labelEl.textContent = 'Medium';
      else if (val === 'low') labelEl.textContent = 'Low';
      else labelEl.textContent = val;
  }
  if (btnEl) {
      if (val) btnEl.classList.add('text-primary');
      else btnEl.classList.remove('text-primary');
  }
};

var currentUploadFile = null;
var currentUploadPrefix = null;
var currentUploadStudentId = null;

window.closePreviewModal = function(prefix) {
  var modal = document.getElementById(prefix + '-preview-modal');
  if (modal) modal.style.display = 'none';
  currentUploadFile = null;
  currentUploadPrefix = null;
  currentUploadStudentId = null;
  
  // Clear file input
  var fileInput = document.getElementById(prefix + '-file-input');
  if (fileInput) fileInput.value = '';
};

window.confirmUpload = function(prefix) {
    if (!currentUploadFile || !currentUploadStudentId) return;
    
    // Extra safety check for invalid ID
    if (String(currentUploadStudentId).trim().toLowerCase() === 'null' || String(currentUploadStudentId).trim().toLowerCase() === 'undefined') {
        alert('Invalid student conversation ID. Please select a conversation again.');
        return;
    }
    
    var caption = document.getElementById(prefix + '-preview-caption').value.trim();
    var hashtag = document.getElementById(prefix + '-preview-hashtag-val').value;
    var priority = document.getElementById(prefix + '-preview-priority-val').value;
    
    var fd = new FormData();
    fd.append('file', currentUploadFile);
    fd.append('message', caption);
    if (hashtag) fd.append('hashtag', hashtag);
    if (priority) fd.append('priority', priority);
    
    // Capture ID locally before closing modal (which clears the global)
    var uploadStudentId = currentUploadStudentId;

    // Show uploading state if needed, or just close modal
    closePreviewModal(prefix);
    
    fetch('/students/conversation/' + uploadStudentId + '/upload/', { 
      method: 'POST', 
      body: fd,
      headers: {
          'X-CSRFToken': getCookie('csrftoken')
      }
    })
    .then(function(r){ return r.json(); })
    .then(function(d){
      if (d && d.ok === false) {
        alert(d.reason || 'Upload failed');
      } else if (d && d.id) {
        // Auto-mark as downloaded for sender
        localStorage.setItem('img_downloaded_' + d.id, 'true');
      }
    })
    .catch(function(e){ 
      console.error(e); 
      alert('Upload error');
    });
};

window.uploadFile = function(inputEl, studentId) {
  if (!inputEl || !inputEl.files || inputEl.files.length === 0) return;
  
  // Normalize ID checking
  var sId = String(studentId || '').trim();
  if (!sId || sId.toLowerCase() === 'null' || sId.toLowerCase() === 'undefined') {
    alert('Please select a student conversation first.');
    inputEl.value = '';
    return;
  }
  
  var file = inputEl.files[0];
  
  if (file.size > 10 * 1024 * 1024) {
    alert('File too large. Max 10MB.');
    inputEl.value = '';
    return;
  }
  
  // Identify prefix from inputEl ID: "{prefix}-file-input"
  var prefix = inputEl.id.replace('-file-input', '');
  
  currentUploadFile = file;
  currentUploadPrefix = prefix;
  currentUploadStudentId = studentId;
  
  var modal = document.getElementById(prefix + '-preview-modal');
  var body = document.getElementById(prefix + '-preview-body');
  var title = document.getElementById(prefix + '-preview-title');
  var caption = document.getElementById(prefix + '-preview-caption');
  
  // Reset fields
  if (caption) caption.value = '';
  selectPreviewHashtag('', prefix);
  selectPreviewPriority('', prefix);
  
  if (modal && body) {
      body.innerHTML = '';
      if (file.type.indexOf('image/') === 0) {
          var reader = new FileReader();
          reader.onload = function(e) {
              body.innerHTML = '<img src="' + e.target.result + '" class="preview-img">';
          };
          reader.readAsDataURL(file);
      } else {
          body.innerHTML = '<div class="preview-file-icon"><i class="fas fa-file fa-3x mb-3"></i><br>' + escapeHTML(file.name) + '<br><small>' + formatFileSize(file.size) + '</small></div>';
      }
      title.textContent = 'Preview'; // Could add file name
      modal.style.display = 'flex';
  }
};

window.updateMessageBubble = function(msg) {
  if (!msg || !msg.id) return;
  var msgTextEl = document.getElementById('msg-text-' + msg.id);
  if (!msgTextEl) return;
  
  var newText = msg.message || '';
  
  // Update text
  msgTextEl.innerText = newText;
  msgTextEl.style.display = 'block';
  
  // Remove edit container if exists
  var editContainer = document.getElementById('edit-container-' + msg.id);
  if (editContainer) editContainer.remove();
  
  // Add edited indicator if missing
  var parent = msgTextEl.parentNode;
  var hasEdited = false;
  var smalls = parent.querySelectorAll('small');
  smalls.forEach(function(s){
    if (s.textContent.indexOf('(edited)') > -1) hasEdited = true;
  });
  
  if (!hasEdited) {
    var editedDiv = document.createElement('div');
    editedDiv.className = 'text-end';
    editedDiv.style.lineHeight = '1';
    editedDiv.innerHTML = '<small style="font-size: 0.7rem; opacity: 0.8;">(edited)</small>';
    parent.appendChild(editedDiv);
  }
};
