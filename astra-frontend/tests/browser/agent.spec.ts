import { test, expect } from '@playwright/test';

async function workspace(page) {
  await page.goto('/');
  await page.getByRole('button', { name: 'Soạn đề', exact: true }).waitFor();
  await page.getByRole('button', { name: 'Soạn đề', exact: true }).click();
  await page.getByRole('button', { name: /Tùy chỉnh đề/ }).click();
}
async function send(page, text: string) {
  await page.getByRole('textbox', { name: 'Yêu cầu soạn đề' }).fill(text);
  await page.getByRole('button', { name: 'Gửi yêu cầu', exact: true }).click();
}

test('real Agent drives sidebar, modal and library; reply survives navigation', async ({ page }) => {
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  await workspace(page);
  await send(page, 'Thu gọn menu');
  await expect(page.getByText('Đã thu gọn menu.', { exact: true })).toBeVisible();
  await expect(page.locator('.app-shell')).toHaveClass(/controls-collapsed/);
  await send(page, 'Mở rộng menu');
  await expect(page.getByText('Đã mở rộng menu.', { exact: true })).toBeVisible();
  await send(page, 'Mở thiết lập đề');
  await expect(page.getByText('Thiết lập đề theo yêu cầu', { exact: true })).toBeVisible();
  await page.keyboard.press('Escape');
  // Close using the modal's real close control if Escape is not supported.
  const modal = page.locator('.modal-overlay');
  if (await modal.isVisible()) await page.getByRole('button', { name: /Đóng/ }).click();
  await send(page, 'Mở Tủ đề');
  await expect(page.getByRole('heading', { name: 'Tủ đề của thầy cô' })).toBeVisible();
  await page.locator('.exam-row').first().click();
  await expect(page.getByText('Đã mở Tủ đề.', { exact: true })).toBeVisible();
  expect(errors).toEqual([]);
});

test('proxy 502 gives recovery instruction; retry keeps one message and one effect', async ({ page }) => {
  await workspace(page);
  await page.route('**/agent/turns', route => route.fulfill({ status: 502, body: '' }));
  await send(page, 'Thu gọn menu');
  await expect(page.getByRole('alert')).toContainText('npm run dev');
  await page.unroute('**/agent/turns');
  await page.getByRole('button', { name: 'Thử lại kết nối' }).click();
  await expect(page.getByText('Đã thu gọn menu.', { exact: true })).toBeVisible();
  await expect(page.getByRole('article').getByText('Thu gọn menu', { exact: true })).toHaveCount(1);
});

test('lost feedback response resumes settlement without creating another workspace', async ({ page }) => {
  await workspace(page);
  await page.route('**/agent/execution-results', route => route.fulfill({ status: 502, body: '' }));
  await send(page, 'Tạo một không gian làm việc mới');
  await expect(page.getByRole('alert')).toContainText('đang chờ Agent xác nhận');
  await page.unroute('**/agent/execution-results');
  await page.getByRole('button', { name: 'Thử lại kết nối' }).click();
  await expect(page.getByText('Đã tạo bản nháp mới.', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Tủ đề', exact: true }).click();
  await expect(page.locator('.exam-row')).toHaveCount(2);
});

test('manual navigation while turn is waiting blocks stale automatic navigation', async ({ page }) => {
  await workspace(page);
  let release!: () => void;
  const gate = new Promise<void>(resolve => { release = resolve; });
  await page.route('**/agent/turns', async route => { await gate; await route.continue(); });
  await send(page, 'Mở Tủ đề');
  await page.getByRole('button', { name: 'Chào thầy cô', exact: true }).click();
  release();
  const receipt = await page.waitForResponse(response => response.url().endsWith('/agent/execution-results'));
  expect(receipt.ok()).toBeTruthy();
  await expect(page.getByRole('heading', { name: 'Tủ đề của thầy cô' })).toHaveCount(0);
});
