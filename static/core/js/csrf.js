(function () {
  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) {
      return parts.pop().split(';').shift();
    }
    return undefined;
  }

  const csrftoken = getCookie('csrftoken');

  function csrfFetch(input, init = {}) {
    const options = {
      credentials: 'same-origin',
      ...init,
      headers: {
        'X-CSRFToken': csrftoken,
        ...(init.headers || {}),
      },
    };
    return fetch(input, options);
  }

  if (typeof window !== 'undefined') {
    window.getCookie = getCookie;
    window.csrftoken = csrftoken;
    window.csrfFetch = csrfFetch;

    if (window.axios) {
      window.axios.defaults.xsrfCookieName = 'csrftoken';
      window.axios.defaults.xsrfHeaderName = 'X-CSRFToken';
      window.axios.defaults.withCredentials = true;
    }
  }
})();
