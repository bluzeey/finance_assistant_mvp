import { expect, test } from '@playwright/test';

test('Ask page renders at desktop and mobile widths', async ({ page }) => {
  await page.goto('/ask');
  await expect(page.getByRole('heading', { name: 'Ask a finance question. Get the number and its proof.' })).toBeVisible();
  await expect(page.getByText('Synthetic demo data')).toBeVisible();
});
