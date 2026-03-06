

## GitHub Push — Limitation

Lovable's GitHub integration syncs the **entire project** as the root of a repository. It cannot push files into a subfolder (`apps/explorex/frontend/`) of an existing repo.

### What you can do instead

**Manual approach (recommended):**
1. Connect the project to GitHub via Lovable (Settings → GitHub → Connect) to create a temporary repo
2. Clone both repos locally
3. Copy the contents of the Lovable repo into `apps/explorex/frontend/` in `javi2481/data-x-claude`
4. Push to `javi2481/data-x-claude`

**Or from Lovable directly:**
1. Connect to GitHub to get a repo with all the code
2. Locally run:
```bash
git clone https://github.com/javi2481/data-x-claude.git
cd data-x-claude
mkdir -p apps/explorex/frontend
# Copy all files from the Lovable-generated repo into apps/explorex/frontend/
git add . && git commit -m "Add explorex frontend" && git push
```

Lovable cannot selectively place files in a subdirectory of an external repo — this requires a local Git operation.

