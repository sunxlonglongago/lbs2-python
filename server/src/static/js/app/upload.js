// Upload frame: port of upload.asp. Loaded in an iframe from the article and
// comment forms; the finished tag is appended to the parent's message box.
import './api.js';
import './render.js';

const R = window.LBSRender;

function formHtml() {
  return '<form id="fform" enctype="multipart/form-data" method="post" ' +
    'action="upload.asp?act=upload" style="display: inline">' +
    '<input name="File" type="file" style="font-size:12px;" size="40" ' +
    'class="text upload-file" />&nbsp;' +
    '<input type="submit" name="Submit" value=" Upload " class="button" />' +
    '</form>';
}

function errorHtml(code, extra) {
  const text = {
    upload: 'Failed to Create Object or Get File Data.',
    size: 'File Size exceeds the Limit. (' + extra + ')',
    type: 'Invalid File Type. (' + extra + ')',
    write: 'Failed to write file.',
  }[code] || code;
  return '<div class="upload-error">' + R.escapeHtml(text) + '&nbsp;' +
    '<input type="button" value=" Back " onClick="window.history.back()" ' +
    'class="button" /></div>';
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

async function main() {
  const mount = R.byId('uploadMount');
  const payload = await LBS.load();
  const user = payload.user;
  const features = payload.site.features || {};
  if (!user || !(user.rights.upload > 0) || !features.upload) {
    mount.textContent = 'You do not have the permission for this operation.';
    return;
  }
  const limits = await LBS.get('/api/upload/limits');
  mount.innerHTML = formHtml();
  const form = R.byId('fform');
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const file = form.File.files[0];
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
        mount.innerHTML = errorHtml(data.error,
          data.error === 'size' ? limits.size + ' bytes' : limits.types.join(','));
        return;
      }
      insertIntoParent(data.ubb);
      mount.innerHTML = '<div class="upload-done">File is Uploaded.&nbsp;' +
        '<input type="button" value=" Back " onclick="window.history.back()" ' +
        'class="button" /></div>';
    } catch (error) {
      mount.innerHTML = errorHtml('write');
    }
  });
}

main();
