package com.lifehearts;

import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;
import net.minecraft.world.item.CreativeModeTabs;
import net.minecraft.world.item.Item;
import net.minecraftforge.event.BuildCreativeModeTabContentsEvent;
import net.minecraftforge.eventbus.api.IEventBus;
import net.minecraftforge.fml.ModLoadingContext;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.config.ModConfig;
import net.minecraftforge.fml.javafmlmod.FMLJavaModLoadingContext;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;
import org.slf4j.Logger;

/**
 * Life Hearts — аддон до Limited Lives. У світі зрідка з'являються живі серця; розбий серце — отримаєш ще одне життя.
 */
@Mod(LifeHearts.MOD_ID)
public class LifeHearts {
    public static final String MOD_ID = "lifehearts";
    public static final Logger LOG = com.mojang.logging.LogUtils.getLogger();

    public static final DeferredRegister<EntityType<?>> ENTITIES = DeferredRegister.create(ForgeRegistries.ENTITY_TYPES, MOD_ID);
    public static final DeferredRegister<Item> ITEMS = DeferredRegister.create(ForgeRegistries.ITEMS, MOD_ID);

    public static final RegistryObject<EntityType<HeartEntity>> HEART = ENTITIES.register("heart",
            () -> EntityType.Builder.<HeartEntity>of(HeartEntity::new, MobCategory.MISC).sized(0.9F, 1.1F)
                    .clientTrackingRange(8).updateInterval(2).fireImmune().build("heart"));
    public static final RegistryObject<Item> SUMMONER = ITEMS.register("heart_summoner",
            () -> new HeartSummonerItem(new Item.Properties().stacksTo(1)));

    public static final RegistryObject<Item> LIFE_HEART = ITEMS.register("life_heart", LifeHeartItem::new);

    public static final DeferredRegister<net.minecraft.world.item.CreativeModeTab> TABS =
            DeferredRegister.create(net.minecraft.core.registries.Registries.CREATIVE_MODE_TAB, MOD_ID);
    public static final RegistryObject<net.minecraft.world.item.CreativeModeTab> TAB = TABS.register("main",
            () -> net.minecraft.world.item.CreativeModeTab.builder()
                    .title(net.minecraft.network.chat.Component.translatable("itemGroup.lifehearts"))
                    .icon(() -> new net.minecraft.world.item.ItemStack(LIFE_HEART.get()))
                    .displayItems((params, out) -> {
                        out.accept(LIFE_HEART.get());
                        out.accept(SUMMONER.get());
                    }).build());

    public LifeHearts() {
        IEventBus bus = FMLJavaModLoadingContext.get().getModEventBus();
        ENTITIES.register(bus);
        ITEMS.register(bus);
        TABS.register(bus);
        bus.addListener(this::tabs);
        ModLoadingContext.get().registerConfig(ModConfig.Type.COMMON, HeartConfig.SPEC);
        Net.register();
    }

    private void tabs(BuildCreativeModeTabContentsEvent e) {
        if (e.getTabKey() == CreativeModeTabs.TOOLS_AND_UTILITIES) {
            e.accept(SUMMONER.get());
        }
    }
}
