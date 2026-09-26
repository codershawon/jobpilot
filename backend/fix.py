p = "alembic/versions/e557283fb2ab_jobs_applications_saved_searches.py"

src = open(p, encoding="utf-8").read()
old = "sa.Column('notify_enabled', sa.Boolean(), nullable=False)"
new = "sa.Column('notify_enabled', sa.Boolean(), nullable=False, server_default=sa.true())"

if old in src:
    open(p, "w", encoding="utf-8").write(src.replace(old, new))
    print("✅ ঠিক হয়েছে")
else:
    print("⚠ পুরনো লাইনটা পাওয়া যায়নি — হয়তো আগেই বদলে গেছে")
    print("server_default আছে?", "server_default" in src)