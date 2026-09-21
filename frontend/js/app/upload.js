// Upload frame: port of upload.asp. Loaded in an iframe from the article and
// comment forms; the finished tag is appended to the parent's message box.
import './api.js';
import './render.js';

const R = window.LBSRender;

let mount = null;
let limits = { size: 0, types: [] };

function formHtml() {
  return '<form id="fform" enctype="multipart/form-data" method="post" ' +
    'action="upload.asp?act=upload" style="display: inline">' +
    '<input name="File" type="file" style="font-size:12px;" size="40" ' +
    'class="text upload-file" />&nbsp;' +
    '<input type="submit" name="Submit" value=" Upload " class="button" />' +
    '</form>';
}

function errorText(code, extra) {
  return {
    upload: 'Failed to Create Object or Get File Data.',
    size: 'File Size exceeds the Limit. (' + extra + ')',
    type: 'Invalid File Type. (' + extra + ')',
    write: 'Failed to write file.',
  }[code] || code;
}

function showForm() {
  mount.innerHTML = formHtml();
  R.byId('fform').addEventListener('submit', submit);
}

// The Back button re-renders this frame so another file can be picked. The ASP
// original called history.back(), which walks the history shared with the
// parent page and rolls back the article or comment being edited there.
function showMessage(className, text) {
  mount.innerHTML = '<div class="' + className + '">' + R.escapeHtml(text) +
    '&nbsp;<input type="button" value=" Back " class="button upload-back" />' +
    '</div>';
  mount.querySelector('.upload-back').addEventListener('click', showForm);
}

function insertIntoParent(markup) {
  try {
    const parentForm = window.parent.document.inputform;
    if (parentForm && parentForm.message) {
      parentForm.message.value += '\n' + markup;
      return true;
    }
  } catch (error) {
    return false;
  }
  return false;
}

async function submit(event) {
  event.preventDefault();
  const file = event.currentTarget.File.files[0];
  if (!file) {
    return;
  }
  const body = new FormData();
  body.append('File', file);
  try {
    const response = await fetch(LBS.api('/api/upload'), {
      method: 'POST',
      credentials: 'same-origin',
      body,
    });
    const data = await response.json();
    if (!data.ok) {
      showMessage('upload-error', errorText(data.error,
        data.error === 'size' ? limits.size + ' bytes' : limits.types.join(',')));
      return;
    }
    insertIntoParent(data.ubb);
    showMessage('upload-done', 'File is Uploaded.');
  } catch (error) {
    showMessage('upload-error', errorText('write'));
  }
}

async function main() {
  mount = R.byId('uploadMount');
  const payload = await LBS.load();
  const user = payload.user;
  const features = payload.site.features || {};
  if (!user || !(user.rights.upload > 0) || !features.upload) {
    mount.textContent = 'You do not have the permission for this operation.';
    return;
  }
  limits = await LBS.get('/api/upload/limits');
  showForm();
}

main();
