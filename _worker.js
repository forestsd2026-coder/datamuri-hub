export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.hostname === 'datamuri-hub.pages.dev' || url.hostname === 'datamuri.us.com') {
      url.hostname = 'www.datamuri.us.com';
      return Response.redirect(url.toString(), 301);
    }

    return env.ASSETS.fetch(request);
  },
};
