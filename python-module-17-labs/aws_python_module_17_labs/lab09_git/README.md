# Lab 09 — Git and GitHub workflow

This lab is a command-line workflow rather than a Python program.

## 1. Check Git

```bash
git --version
```

## 2. Initialize a repository

Run these commands from the project folder:

```bash
git init
git status
git add .
git commit -m "Add Python practice labs"
```

## 3. Connect a GitHub repository

Create an empty repository in your own GitHub account, then replace the URL below with your repository URL:

```bash
git branch -M main
git remote add origin https://github.com/USERNAME/REPOSITORY.git
git remote -v
git push -u origin main
```

## 4. Update after future practice

```bash
git status
git add .
git commit -m "Complete another Python exercise"
git push
```

Never place passwords, access keys, learner-lab credentials, or `.env` files in Git. Use a private repository when your training provider's terms do not permit public redistribution of its materials.
