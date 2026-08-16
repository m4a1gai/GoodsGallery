import enum


class SourceKind(str, enum.Enum):
    official = "official"
    manufacturer = "manufacturer"
    retailer = "retailer"
    secondhand = "secondhand"
    search = "search"
    user_submitted = "user_submitted"


class CrawlPolicy(str, enum.Enum):
    auto = "auto"
    search_discovery_only = "search_discovery_only"
    manual_import_only = "manual_import_only"
    disabled = "disabled"


class CandidateStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"
    merged = "merged"
    split = "split"


class DuplicateReviewStatus(str, enum.Enum):
    pending = "pending"
    same = "same"
    different = "different"


class CollectionStatus(str, enum.Enum):
    owned = "owned"
    wishlist = "wishlist"
    not_owned = "not_owned"


class DataOrigin(str, enum.Enum):
    crawler = "crawler"
    manual = "manual"
    ai = "ai"
    import_ = "import"
