"""Build a deterministic script solely from validated catalog facts."""


def build_script(product, template):
    facts = [
        f'{product["servings"]} порций',
        f'{product["package_weight_g"]} г в упаковке',
        f'по {product["dosage_g_per_drink"]} г на напиток',
        f'объём напитка {product["drink_volume_ml"]} мл',
        f'произведено в {product["country_of_origin"]}',
        product["positioning"],
    ]
    product_label = f'{product["name"]} {product["brand"]}'
    script = (
        f'{product["servings"]} порций Bubble Tea дома из одной упаковки. '
        f'В упаковке {product["package_weight_g"]} г: {product_label} — '
        f'по {product["dosage_g_per_drink"]} г на напиток объёмом '
        f'{product["drink_volume_ml"]} мл. Приготовьте напиток по инструкции на упаковке. '
        f'Произведено в {product["country_of_origin"]}. {product["positioning"]}.'
    )
    return {
        "title": f'{product["name"]} — {product["servings"]} порций дома',
        "script": script,
        "description": f'{product["name"]} {product["brand"]} для домашнего приготовления Bubble Tea.',
        "facts_used": facts,
        "product_id": product["id"],
        "template_id": template["id"],
    }
