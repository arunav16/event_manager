# Event Manager API - Final Assignment Submission

## 🔧 Closed Issues and Contributions

Below are the five resolved issues, each including linked test cases and the corresponding application code modifications:

1. ✅ [Nickname Mismatch](https://github.com/arunav16/event_manager/issues/1)
2. ✅ [Duplicate Nickname](https://github.com/arunav16/event_manager/issues/4)
3. ✅ [Email Verification](https://github.com/arunav16/event_manager/issues/6)
4. ✅ [URL Validation](https://github.com/arunav16/event_manager/issues/8)
5. ✅ [Updation Edge Cases](https://github.com/arunav16/event_manager/issues/11)
6. ✅ [Requirements Conflict and Security Issues](https://github.com/arunav16/event_manager/issues/13)

All issues were closed after thorough testing, validation, and merging into the `main` branch using Git best practices.

---

## 🐳 DockerHub Deployment

- **Docker Image**: [View on DockerHub](https://hub.docker.com/repository/docker/arunav16/event_manager/general)

This project is built and pushed automatically to DockerHub using GitHub Actions defined in `production.yml`, supporting multi-platform builds and vulnerability scanning with Trivy.

---

## ✍️ Reflection

Through this assignment, I gained practical experience in applying CI/CD practices using GitHub Actions and Docker. I learned how to manage test environments with PostgreSQL in CI, resolve dependency conflicts (`pyasn1` vs `python-jose`), and structure workflows to build, test, and push Docker images efficiently.

Tackling issues like edge case validation, nickname uniqueness, and external URL schema validation helped reinforce my understanding of both backend validation and asynchronous database interactions with SQLAlchemy. Additionally, collaborating through pull requests and managing issues in a GitHub project simulated a real-world software development workflow, which will be invaluable in team-based environments.

---

✅ **All issues merged into `main` and tested successfully.**
