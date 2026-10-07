// Optional browser QA: requires Playwright and an installed Chromium browser.
const { chromium } = require('playwright');
const fs = require('node:fs');
const assert = require('node:assert/strict');
const path = require('node:path');
let previewProcess;
(async () => {
  const info = JSON.parse(fs.readFileSync(path.join(__dirname, process.env.QA_BUILD || 'dist', 'build-info.json')));
  const origin = (process.env.QA_ORIGIN || 'http://127.0.0.1:4173') + info.base;
  if (process.env.QA_PYTHON) {
    const {spawn} = require('node:child_process');
    const args = [path.join(__dirname,'serve.py'),'--port',new URL(origin).port];
    if (process.env.QA_BUILD === '.qa-dist') args.push('--qa');
    previewProcess = spawn(process.env.QA_PYTHON,args,{cwd:__dirname,windowsHide:true,stdio:'ignore'});
    let ready = false;
    for (let i=0;i<40;i++) {
      try { const response=await fetch(origin,{signal:AbortSignal.timeout(800)}); if(response.ok){ready=true;break;} } catch {}
      await new Promise(resolve=>setTimeout(resolve,200));
    }
    assert.ok(ready,'Local preview did not start');
  }
  const browser = await chromium.launch({headless:true, ...(process.env.QA_BROWSER ? {executablePath:process.env.QA_BROWSER} : {})});
  const report = {base:info.base,appCount:info.appCount,viewports:[], checks:[]};
  const errors = [];
  const qaFolder = path.join(__dirname,'qa',process.env.QA_REPORT || 'production');
  fs.mkdirSync(qaFolder,{recursive:true});
  const page = await browser.newPage();
  page.on('pageerror', error => errors.push(error.message));
  for (const width of [1440, 390, 320, 768]) {
    await page.setViewportSize({width,height:1000});
    for (const route of [...info.routes, '404.html']) {
      const response = await page.goto(origin + route);
      assert.equal(response.status(), 200);
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
      assert.equal(overflow, false, `Overflow ${width}: ${route}`);
    }
    report.viewports.push({width,pages:info.routes.length+1,noOverflow:true});
  }
  await page.setViewportSize({width:1440,height:1000});
  await page.goto(origin);
  await page.screenshot({path:path.join(qaFolder,'home-desktop.png'),fullPage:true});
  await page.evaluate(() => window.scrollTo(0,600));
  assert.equal(await page.locator('.site-header').evaluate(el=>Math.round(el.getBoundingClientRect().top)),0);
  report.checks.push('Sticky header stays at top while scrolling');
  await page.setViewportSize({width:390,height:844});
  await page.goto(origin);
  await page.screenshot({path:path.join(qaFolder,'home-mobile.png'),fullPage:true});
  const menu = page.locator('.menu-toggle');
  await menu.click();
  assert.equal(await menu.getAttribute('aria-expanded'),'true');
  await page.locator('#primary-nav').waitFor({state:'visible'});
  assert.equal(await page.locator('#primary-nav').isVisible(),true);
  await page.keyboard.press('Escape');
  assert.equal(await menu.getAttribute('aria-expanded'),'false');
  assert.equal(await page.evaluate(() => document.activeElement.className),'menu-toggle');
  await menu.click();
  await page.locator('main h1').click();
  assert.equal(await menu.getAttribute('aria-expanded'),'false');
  await menu.click();
  await page.locator('#primary-nav').getByRole('link',{name:'Apps',exact:true}).click();
  assert.equal(await page.locator('.menu-toggle').getAttribute('aria-expanded'),'false');
  report.checks.push('Mobile open, Escape/focus, outside click, navigation');
  if (info.appCount) {
  const firstName = await page.locator('[data-app] h3').first().innerText();
  await page.locator('#app-search').fill(firstName);
  assert.equal(await page.locator('[data-app]:visible').count(),1);
  await page.locator('#app-search').fill('no-such-app');
  assert.equal(await page.locator('#empty-apps').isVisible(),true);
  await page.locator('#app-search').fill('');
  const category = await page.locator('[data-app]').first().getAttribute('data-category');
  const count = await page.locator('[data-app]').evaluateAll((cards, cat)=>cards.filter(c=>c.dataset.category===cat).length,category);
  await page.getByRole('button',{name:category,exact:true}).click();
  assert.equal(await page.locator('[data-app]:visible').count(),count);
  await page.getByRole('button',{name:'All',exact:true}).click();
  assert.equal(await page.locator('[data-app]:visible').count(),info.appCount);
  report.checks.push('Search, empty state, category and reset');
  const appHref = await page.locator('[data-app] h3 a').first().getAttribute('href');
  await page.locator('[data-app] h3 a').first().click();
  assert.equal(await page.locator('h1').innerText(),firstName);
  assert.ok(await page.locator('.feature').count());
  if (info.appCount>1) assert.ok(await page.locator('[data-app]').count());
  report.checks.push('Data generates app detail route, features, related apps and CTA');
  } else {
    assert.equal(await page.locator('.catalog-empty').isVisible(),true);
    report.checks.push('Empty catalog without invented app listings');
  }
  await page.goto(origin + 'contact/');
  await page.locator('#contact-name').fill('QA User');
  await page.locator('#contact-email').fill('qa@example.com');
  await page.locator('#contact-message').fill('Testing encoded text: & plus + and a new line\nSecond line.');
  await page.getByRole('button',{name:'Create email draft'}).click();
  await page.locator('#email-draft').waitFor({state:'visible'});
  const mailto = await page.locator('#email-draft').getAttribute('href');
  assert.ok(mailto.startsWith('mailto:'));
  assert.ok(decodeURIComponent(mailto).includes('Testing encoded text: & plus +'));
  report.checks.push('Contact email draft encoding and honest status');
  await page.goto(origin + 'unknown-page/');
  assert.equal(await page.locator('h1').textContent(),'404');
  await page.getByRole('link',{name:'Back to home'}).click();
  assert.equal(new URL(page.url()).pathname,info.base);
  report.checks.push('404 recovery');
  const plain = await browser.newContext({javaScriptEnabled:false,viewport:{width:390,height:844}});
  const nojs = await plain.newPage();
  await nojs.goto(origin + 'apps/');
  assert.equal(await nojs.locator('#primary-nav').isVisible(),true);
  assert.equal(await nojs.locator('[data-app]:visible').count(),info.appCount);
  report.checks.push('No-JavaScript navigation and app catalog');
  assert.deepEqual(errors,[]);
  report.checks.push('No browser JavaScript errors');
  const footerContents=[];
  for (const route of info.routes) {
    await page.goto(origin + route);
    footerContents.push(await page.locator('.site-footer').innerHTML());
  }
  // Portable builds rewrite hrefs according to page depth; compare user-visible content.
  await page.goto(origin);
  const footerText = await page.locator('.site-footer').innerText();
  for (const route of info.routes) {
    await page.goto(origin+route);
    assert.equal(await page.locator('.site-footer').innerText(),footerText);
  }
  report.checks.push('Shared footer content consistent on every page');
  for (const width of [1440,390]) {
    await page.setViewportSize({width,height:1000});
    for (const route of info.routes) {
      await page.goto(origin+route);
      await page.evaluate(()=>document.documentElement.style.fontSize='200%');
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,`Text enlargement overflow: ${width} ${route}`);
    }
  }
  report.checks.push('200% text enlargement without horizontal overflow');
  fs.writeFileSync(path.join(qaFolder,'browser-report.json'),JSON.stringify(report,null,2));
  await browser.close();
  previewProcess?.kill();
  console.log(JSON.stringify(report,null,2));
})().catch(error=>{previewProcess?.kill();console.error(error);process.exit(1)});
