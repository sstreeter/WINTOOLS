# Git Quick Reference for IconForge

## Current Status

Your IconForge project is now under Git version control! 🎉

**Initial commit:** `14c9b79` - IconForge v1.0 with all features

---

## Common Git Commands

### Check Status
```bash
git status
```
Shows what files have changed since last commit.

### View Commit History
```bash
git log --oneline
```
Shows all commits in a compact format.

### Make a Commit
```bash
# Stage all changes
git add -A

# Commit with message
git commit -m "Description of changes"
```

### Revert to Previous Version
```bash
# See commit history
git log --oneline

# Revert to specific commit (replace COMMIT_HASH)
git checkout COMMIT_HASH

# Or go back to latest
git checkout master
```

### Create a Backup Branch
```bash
# Before making risky changes
git branch backup-before-changes

# List all branches
git branch -a
```

### Undo Uncommitted Changes
```bash
# Undo all changes since last commit
git reset --hard HEAD

# Undo changes to specific file
git checkout -- filename.py
```

---

## Recommended Workflow

### 1. Before Making Changes
```bash
# Create a backup branch
git branch backup-$(date +%Y%m%d)

# Or just commit current state
git add -A
git commit -m "Working state before changes"
```

### 2. After Making Changes
```bash
# Check what changed
git status
git diff

# Commit changes
git add -A
git commit -m "Added new feature X"
```

### 3. If Something Breaks
```bash
# See recent commits
git log --oneline -n 10

# Revert to working version
git checkout GOOD_COMMIT_HASH

# Or undo last commit (keep changes)
git reset --soft HEAD~1
```

---

## Pushing to GitHub

When you're ready to push to GitHub:

```bash
# Create repo on GitHub first, then:
git remote add origin https://github.com/YOUR_USERNAME/icon-factory.git
git branch -M main
git push -u origin main
```

---

## Useful Aliases

Add these to your `~/.gitconfig` for shortcuts:

```ini
[alias]
    st = status
    co = checkout
    ci = commit
    br = branch
    unstage = reset HEAD --
    last = log -1 HEAD
    visual = log --oneline --graph --all
```

Then use: `git st` instead of `git status`, etc.

---

## Current Repository Info

- **Branch:** `main`
- **Files tracked:** 20 files, 2421 lines of code
- **Initial commit:** IconForge v1.0

**You can now safely experiment and revert changes!** 🚀
