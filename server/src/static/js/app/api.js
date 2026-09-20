// Shared API client for the ported LBS^2 frontend.
// Every dynamic value comes from /api/*; nothing is rendered server side.
const LBS = (() => {
  let strings = {};
  let sitePayload = null;
  let requests = 0;

  // The backend strips a trailing .asp in the WSGI layer, so every API call
  // carries the suffix to keep the original ASP URL look.
  function aspify(path) {
    if (String(path).indexOf('/api/') !== 0) {
      return path;
    }
    const parts = String(path).split('?');
    return parts[0] + '.asp' + (parts[1] ? '?' + parts[1] : '');
  }

  async function request(path, options) {
    requests += 1;
    const response = await fetch(aspify(path), Object.assign({ credentials: 'same-origin' }, options));
    let data = null;
    try {
      data = await response.json();
    } catch (error) {
      data = { ok: false, error: 'bad_response' };
    }
    if (!response.ok) {
      const failure = new Error(data.error || 'http_' + response.status);
      failure.status = response.status;
      failure.data = data;
      throw failure;
    }
    return data;
  }

  return {
    api: aspify,
    get(path) {
      return request(path);
    },
    post(path, body) {
      return request(path, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body || {}),
      });
    },
    patch(path, body) {
      return request(path, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body || {}),
      });
    },
    async load() {
      const [langData, siteData] = await Promise.all([
        request('/api/lang'),
        request('/api/site'),
      ]);
      strings = langData.strings || {};
      sitePayload = siteData;
      return sitePayload;
    },
    t(key) {
      return Object.prototype.hasOwnProperty.call(strings, key) ? strings[key] : key;
    },
    get data() {
      return sitePayload;
    },
    get info() {
      return sitePayload ? sitePayload.site : null;
    },
    get user() {
      return sitePayload ? sitePayload.user : null;
    },
    get sidebar() {
      return sitePayload ? sitePayload.sidebar : null;
    },
    get counters() {
      return sitePayload ? sitePayload.counters : {};
    },
    get requests() {
      return requests;
    },
  };
})();

window.LBS = LBS;
