# Custom Domain Runbook

The site does **not** require a custom domain to launch. The default project URL is sufficient for initial public V&V:

`https://luckygithub777.github.io/nootropics-map/`

The generated `_site/` also works unchanged at a custom-domain root because its runtime asset/data references are relative.

## Domain decision boundary

No domain is hard-coded into v0.1. A domain should be selected only after ownership, brand fit, DNS control, and publication authority are verified. Do not purchase, transfer, or point a domain merely because the repository is ready.

## Secure custom-domain sequence

1. Verify domain ownership in the intended GitHub account before pointing DNS.
2. Add the custom domain in the repository's **Settings → Pages** first.
3. Only then change DNS at the domain provider.
4. For an Actions-published Pages site, follow GitHub's current instructions rather than adding legacy files by assumption.
5. For a subdomain such as `map.example.com`, point its CNAME to `LuckyGitHub777.github.io` — not to a path containing the repository name.
6. For an apex domain, use GitHub's currently documented Pages A/AAAA values or a supported ALIAS/ANAME configuration; verify current values immediately before DNS changes.
7. Do not use wildcard DNS for Pages.
8. After DNS and certificate provisioning succeed, enable **Enforce HTTPS**.
9. Verify canonical host, redirects, certificate, mobile/desktop rendering, and source links.

## Rollback

If domain verification or HTTPS fails, remove/update the DNS mapping before abandoning or changing the GitHub Pages custom-domain setting. Preserve the last known-good Pages URL as the fallback.

## References

- https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site
- https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site
- https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site
