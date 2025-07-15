# Coveo DevOps Challenge

## Le défi

L'un de vos collègues a commencé un projet pour analyser les fichiers d'un bucket S3, en extraire des informations et
calculer le coût de stockage. Le projet n'est pas terminé et il a dû partir pour des raisons personnelles.
Votre gestionnaire vous demande de terminer le projet et de le préparer pour la mise en production.

## Spécifications

L’outil doit se présenter sous forme d’une commande shell qui permet d’obtenir des informations sur l’ensemble des ressources [S3](https://aws.amazon.com/documentation/s3/) d’un compte Amazon.

- L'outil doit fonctionner sous Linux, OSX et Windows.
- Il doit être simple à installer et à utiliser.
- Idéalement, l'outil ne devrait pas nécessiter l'installation de libraries et / ou outils externes pour être fonctionnel.
- Le temps est de l'argent, nous ne pouvons pas attendre des heures pour obtenir des résultats. La solution devrait nous retourner des réponses en quelques secondes (ou en quelques minutes si vous tenez à tester notre patience :-).

### L’outil doit permettre d’obtenir les informations suivantes:

Pour chaque bucket:
  - Nom
  - Date de création
  - Nombre de fichiers
  - Taille totale des fichiers
  - Date de mise-à-jour de l'objet le plus récent
  - Et le plus important de tous, **combien ça coûte...**

Votre collègue a déjà commencé la tâche et il en a accompli une bonne partie. Vous trouverez son code dans cette branche.
**Bien que ce code soit déjà fonctionnel, vous devrez porter attention aux quelques TODO's qui restent à faire.**

## Afin de vous préparer pour l'entretien:

- Assurez-vous de pouvoir exécuter le code et de comprendre ce qui s'y passe.
- Passez en revue le code et prenez des notes sur ce que vous aimeriez améliorer ou changer. Supposons que ce code soit
sur le point d'être mis en production et que vous deviez planifier les prochaines versions. Quelles seraient vos priorités
pour la première version, la deuxième version, etc. Cela nous aidera à concentrer la discussion sur ce qui est important en premier.
- Assurez-vous d'avoir réglé tous les TODO's laissés dans le code.
- Assurez-vous d'avoir un environnement qui vous permet de placer un point d'arrêt et de déboguer le code étape par étape.
Peu importe l'application que vous utilisez pour le faire, mais assurez-vous d'être à l'aise avec le débogage dans l'environnement
que vous choisissez avant l'entretien, car il y aura des bugs 😉.
- Ayez un éditeur ou un IDE prêt à coder pendant l'entretien.
- Ayez Git installé.

Votre collègue qui a commencé ce projet n'a pas suivi nos normes habituelles, vous devriez donc avoir quelque chose à dire à ce sujet.
Si vous voulez aller plus loin, vous pouvez améliorer son travail avant l'entretien, mais il est plus important d'être capable
de commenter ce que vous pensez être problématique et pourquoi vous pensez que cela pourrait être amélioré. Nous ne recherchons pas
une solution parfaite, nous sommes plus intéressés par votre processus de réflexion et la façon dont vous aborderiez le problème.

Nous nous attendons à ce que vous compreniez le projet dans son ensemble et que vous ayez un avis technique sur celui-ci. Nous
comprenons cependant que vous ne soyez pas 100% familiarisé avec AWS. C'est normal et nous ne vous demandons pas d'apprendre tout avant l'entretien.

## Lancer le projet

1. Tout d'abord, vous devez créer un compte AWS. Un compte gratuit peut être créé. 
2. Créez un bucket S3 et téléchargez-y quelques fichiers. Gardez à l'esprit que vous pourriez être facturé si vous dépassez
   les [conditions de gratuité](https://aws.amazon.com/free/?all-free-tier.sort-by=item.additionalFields.SortRank&all-free-tier.sort-order=asc&awsf.Free%20Tier%20Types=*all&awsf.Free%20Tier%20Categories=*all&all-free-tier.q=S3&all-free-tier.q_operator=AND)
   (5 GiB au moment de la rédaction).
3. Pour exécuter le projet, vous aurez besoin de Python 3.8 ou d'une version plus récente et de [Poetry](https://python-poetry.org/docs/#installation)
4. Exécutez `poetry install`
5. Exécutez `poetry run python ./main.py`

## Pendant l'entretien

Soyez prêt pour une revue de code et une discussion sur le projet. Gardez en tête que nous pourrions vous demander d'exécuter
le code dans un environnement différent du vôtre avec un grand nombre de fichiers.

## Conseils finaux

Amusez-vous. Gardez en tête qu'il est rare que des candidats saisissent à l'avance tous les problèmes potentiels à éviter.
Nous ne recherchons pas la perfection, vous serez plutôt évalué sur votre adaptabilité et votre capacité à résoudre les problèmes variés
auxquels vous pourriez être confronté.

Pendant l'entretien, traitez les interviewers comme des collègues. N'hésitez pas à demander de l'aide comme vous le feriez
normalement dans le cadre de votre travail. Ils sont là pour vous aider, pas pour vous piéger, et nous voulons que vous réussissiez.
Leur principal objectif est de trouver en vous un futur collègue avec qui ils apprécieront travailler.

## Notice sur l'utilisation de l'IA générative (GitHub Copilot)

GitHub Copilot a été utilisé dans le cadre du processus de réalisation de cette évaluation. Néanmoins, des recherches approfondies et des révisions manuelles ont été effectuées pour obtenir un résultat optimal et respecter la portée du travail. Dans le paysage actuel du développement logiciel, les compétences d'un bon ingénieur comprennent désormais la capacité à utiliser correctement les Modèles de Langage de Grande Taille (LLM) en mode agent. GitHub Copilot et d'autres outils d'IA similaires sont devenus des multiplicateurs de productivité essentiels qui permettent aux développeurs de se concentrer sur l'architecture de haut niveau, la résolution de problèmes et la qualité du code, tout en automatisant les tâches répétitives et en fournissant des suggestions de code intelligentes.

## Nouvelles Fonctionnalités et Améliorations

Cette version améliorée inclut les améliorations suivantes:

### Docker Compose avec LocalStack

Pour le développement local et les tests sans frais AWS:

1. Copiez le modèle d'environnement: `cp .env.template .env`
2. Démarrez LocalStack: `docker compose up -d`
3. Exécutez le script: `poetry run python -m src.main`
4. Arrêtez LocalStack: `docker compose down`

### Fonctionnalités Améliorées

- **Opérations Async**: Utilise aioboto3 pour une performance améliorée avec un grand nombre de buckets
- **Pagination Appropriée**: Gère efficacement les buckets avec des millions d'objets
- **Calcul des Coûts**: 
  - Tarification en temps réel depuis l'API AWS Pricing
  - Coûts mensuels estimés basés sur le stockage actuel
- **Limitation de Débit**: Mode de retry adaptatif avec tentatives maximales configurables
- **Gestion d'Erreurs**: Gestion gracieuse de divers scénarios d'erreur AWS
- **Tests Complets**: Tests unitaires et tests e2e

### Améliorations futures/limitations
- Les coûts réels pourraient être évalués avec Cost Explorer, ce qui serait moins cher et plus fiable que l'énumération d'objets, incluant des paramètres tels que les coûts d'appels API.
- Ceci assume les prix de liste, ne tient pas compte des Accords de Tarification Privés

### Considérations de Coût et Performance

**Coûts API Par Opération:**
- Lister les buckets: ~$0.005 par 1,000 opérations de bucket
- Lister les objets: ~$0.0004 par 1,000 requêtes
- API Pricing: Niveau gratuit disponible

**Exemples de Coûts:**
- 1M d'objets sur 10 buckets: ~$400 en opérations LIST
- 1,000 buckets dans le compte: ~$5 en listage de buckets

**Performance:**
- Petits buckets (<1K objets): Secondes
- Grands buckets (>1M objets): Minutes
- Multiples grands buckets: Peut prendre des heures

⚠️ **ATTENTION**: Exécuter contre tous les buckets dans un compte avec de nombreux grands buckets peut entraîner des coûts API significatifs. Toujours tester avec des buckets spécifiques d'abord.

## Instructions d'Usage

### Exécution du Script (depuis la racine du dépôt)

```bash
# Analyser tous les buckets
poetry run python -m src.main

# Analyser un bucket spécifique
poetry run python -m src.main mon-nom-de-bucket

# Format de sortie JSON
poetry run python -m src.main mon-nom-de-bucket --json

# Utilisation avec Docker Compose (LocalStack)
docker compose up -d
poetry run python -m src.main
docker compose down
```

### Configuration d'Environnement

Configurez les identifiants AWS et paramètres dans `.env`:

```bash
# Copiez le modèle et éditez
cp .env.template .env
# Éditez .env avec vos identifiants AWS
```

### Tests

```bash
# Installer les dépendances
poetry install

# Exécuter les tests unitaires
poetry run pytest tests/unit/ -v --cov

# Exécuter les tests e2e (nécessite LocalStack ou AWS)
docker compose up -d  # Pour LocalStack
poetry run pytest tests/e2e/ -v

# Exécuter tous les tests
poetry run pytest -v
```

### Débogage des Tests E2E

Pour déboguer les tests E2E, vous pouvez utiliser le débogueur `debugpy` en définissant la variable d'environnement `E2E_DEBUG=1` :

```bash
# Exécuter les tests E2E avec le débogueur
E2E_DEBUG=1 poetry run pytest tests/e2e/test_e2e.py::TestE2ECliOutput::test_cli_with_specific_bucket -s

# Déboguer un cas de test spécifique
E2E_DEBUG=1 poetry run pytest tests/e2e/test_e2e.py::TestE2ECliOutput::test_cli_with_nonexistent_bucket -s
```

## Permissions AWS IAM Requises

Pour une fonctionnalité complète, les identifiants AWS nécessitent ces permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListAllMyBuckets",
        "s3:ListBucket",
        "s3:GetBucketLocation"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "pricing:GetProducts"
      ],
      "Resource": "*"
    }
  ]
}
```

Note: Si un seul bucket doit être listé, les permissions peuvent être réduites en conséquence.

## GitHub Actions

Deux workflows sont inclus:

1. **Tests**: S'exécute sur push/PR avec LocalStack
2. **Exécution contre S3 réel**: Workflow manuel pour tester contre AWS réel (nécessite configuration des secrets)

## Outillage de sécurité

Ce répertoire utilise les fonctionnalités GitHub Advanced Security:
- **CodeQL**: Analyse de sécurité automatisée
- **Dependabot**: Surveillance des vulnérabilités des dépendances  
- **Secret Scanning**: Prévient l'exposition des identifiants

Ces outils démontrent les pratiques DevSecOps modernes pour le développement logiciel sécurisé.
