/**
 * Consent-banner + third-party suppression for Playwright test runs.
 *
 * Why: cookie banners (Cookiebot et al.) overlay the page and intercept every
 * click, so scripts that don't handle them burn 20s-per-click timeouts. Worse,
 * click-accepting "allow all" on a PRODUCTION site makes the test fire real
 * GA4/Ads/Clarity/Pinterest events, polluting the client's analytics.
 * Banners also differ per host (www shows one, *.vercel.app previews often
 * don't), so scripts break exactly when switching environments.
 *
 * Default strategy: block the consent + analytics scripts at the network level
 * BEFORE navigation. No banner is ever injected, no marketing beacons fire,
 * works identically on every host. Import and call on the CONTEXT, pre-goto:
 *
 *   import { suppressThirdParties } from '<this-skill>/helpers/consent.mjs';
 *   const context = await browser.newContext({ ... });
 *   await suppressThirdParties(context);
 *   const page = await context.newPage();
 *
 * Only when consented behavior is itself under test (do GTM tags fire, does
 * the pixel load): skip suppression and use acceptCookiebot(page) instead.
 */

/** Hosts that inject consent UIs or receive marketing/analytics beacons. */
export const THIRD_PARTY_BLOCKLIST = [
	// consent platforms (the banner itself)
	'**/*cookiebot.com/**',
	'**/*cookielaw.org/**', // OneTrust
	'**/*onetrust.com/**',
	'**/*usercentrics.eu/**',
	'**/*consensu.org/**',
	// tag managers + analytics + ads (keep tests out of client analytics!)
	'**/*googletagmanager.com/**',
	'**/*google-analytics.com/**',
	'**/*analytics.google.com/**',
	'**/*doubleclick.net/**',
	'**/*googleadservices.com/**',
	'**/*google.com/ccm/**',
	'**/*google.com/rmkt/**',
	'**/*clarity.ms/**',
	'**/*pinterest.com/**',
	'**/*pinimg.com/ct/**',
	'**/*facebook.net/**',
	'**/*facebook.com/tr/**',
	'**/*bing.com/**',
	'**/*hotjar.com/**',
	// site-specific tag proxies (server-side GTM endpoints)
	'**/tagging.*/**', // e.g. tagging.verlichting.nl
];

/**
 * Abort all consent + analytics requests for the whole browser context.
 * Call BEFORE the first page.goto().
 */
export async function suppressThirdParties(context, extraPatterns = []) {
	for (const pattern of [...THIRD_PARTY_BLOCKLIST, ...extraPatterns]) {
		await context.route(pattern, (route) => route.abort());
	}
}

/**
 * Fallback for runs that NEED real consent: robustly accept a Cookiebot
 * banner if it shows up, and wait until the overlay is really gone.
 * Cookiebot renders different button ids per template/config, so match them all.
 * Returns true if a banner was accepted, false if none appeared.
 */
export async function acceptCookiebot(page, { timeout = 8000 } = {}) {
	const accept = page.locator(
		[
			'#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll',
			'#CybotCookiebotDialogBodyButtonAccept',
			'#CybotCookiebotDialogBodyLevelButtonAccept', // template used on www.verlichting.nl
		].join(', ')
	);
	try {
		await accept.first().waitFor({ timeout });
		await accept.first().click();
		await page.locator('#CybotCookiebotDialog').waitFor({ state: 'hidden', timeout });
		return true;
	} catch {
		return false; // no banner on this host (e.g. *.vercel.app preview) - fine
	}
}
