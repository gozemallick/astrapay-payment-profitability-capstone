# GitLab/GitHub beginner submission steps

## GitLab preferred because assignment asks for MR
1. Create a free GitLab account.
2. Create a new private project named `astrapay-capstone`.
3. Download/unzip the capstone folder on your laptop.
4. Open terminal in that folder.
5. Run:

```bash
git init
git checkout -b feature/payment-profitability-diagnostic
git add .
git commit -m "feat: add synthetic capstone dataset"
git commit --allow-empty -m "docs: add problem framing and data contract"
git commit --allow-empty -m "test: add dq checks and reconciliation"
git commit --allow-empty -m "feat: add profitability model and root-cause analysis"
git commit --allow-empty -m "docs: add executive recommendation and submission notes"
git remote add origin <paste-your-gitlab-project-url>
git push -u origin feature/payment-profitability-diagnostic
```

6. Open GitLab project page.
7. Click **Create merge request**.
8. Paste the contents of `09_GitLab_MR/MR_description.md` into the MR description.
9. Ask one colleague to review and leave one actual comment if peer-review evidence is mandatory.

## GitHub alternative
Same process, but create a Pull Request instead of Merge Request. If trainer accepts GitHub, mention that GitHub PR is equivalent to GitLab MR for branch-based review.
