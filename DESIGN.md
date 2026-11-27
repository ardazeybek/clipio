# DESIGN.md — Clipio görsel dili

Kaynak: `clipio/ui/components/Theme.qml`. README görselleri `docs/assets/src/base.css` ile aynı değerleri kullanır.

## Yön
Eski defter kâğıdı: sıcak krem zemin, yapışkan bant, kurşun kalem noktaları, şeftali vurgu. Sade, yumuşak, oyuncak gibi değil.

## Renkler
| Token | Değer | Kullanım |
|---|---|---|
| paper | `#F6EFE1` | panel zemini |
| sheet | `#FFFCF5` | kart |
| edge | `#E4D8C2` | kâğıt kenarı |
| stack | `#E9DFCB` | kart altı gölge yığını |
| dots | `#C9BBA4` | noktalar, tuş kenarı |
| ink / ink-2 / pencil | `#3D3530` / `#6B5F55` / `#9A8E7E` | metin seviyeleri |
| accent / accent-dk / accent-soft | `#E58F6F` / `#C97556` / `#F8DDD1` | ana vurgu (şeftali) |
| tape | `#F3D9A4` | hardal bant |
| sage / sage-dk / sage-soft | `#9CC3A6` / `#5E8C6A` / `#DCEBDF` | sabitlenmiş öğe |

## Yazı
- Başlık + gövde: **Nunito** (600–900)
- Kod / kısayol: **JetBrains Mono** (500–700)

## Biçim
- Panel köşesi 26px, 2px kenar, `8px 8px 0` düz yığın gölgesi (blur yok)
- Kart içinde kart yok; mor gradyan yok
