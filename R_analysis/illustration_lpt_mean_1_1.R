#working folder & packages#####
#set R Working Folder
working_directory = "/home/felix/git/file_placement2/paper/figures/plots"
input_file = "/home/felix/git/file_placement2/paper/figures/plots/osds_10_caps_100_bws_1_split_sizes_100_0.67_reps_1.csv"
output_file_name = "osds_10_caps_100_bws_1_split_sizes_100_0.67_reps_1_1000"

unit_conversion_factor = 1 #/ (1024 * 1024) #/(1000 * 60)

setwd(working_directory)
#use install.packages()
library(ggplot2)
library(reshape)
#fuer farbauswahl   display.brewer.all()
library(RColorBrewer) 
library(Rmisc)
#more detailed read_csv()
library(readr) 

# distr_pair_id, initial_type, rebalancing_mechanism, rebalanced, osd_id, osd_load

df <- read_csv(input_file,
               col_types = cols(X1 = col_skip(),
                                distr_pair_id = col_double(),
                                initial_type = col_factor(levels = c("totrand", "rand_r_r", "caprand")),
                                rebalancing_mechanism = col_character(),
                                lpt_factor = col_double(),
                                rebalanced = col_character(),
                                osd_id = col_character(),
                                moved = col_character(),
                                osd_load = col_double()
                                ))

# generate pretty OSD names
osd_lables <- c(osd_104857600_0 = "OSD 0", osd_104857600_1 = "OSD 1", osd_104857600_2 = "OSD 2", osd_104857600_3 = "OSD 3", 
                osd_104857600_4 = "OSD 4", osd_104857600_5 = "OSD 5", osd_104857600_6 = "OSD 6", osd_104857600_7 = "OSD 7", 
                osd_104857600_8 = "OSD 8", osd_104857600_9 = "OSD 9", osd_104857600_10 = "OSD 10", osd_104857600_11 = "OSD 11")
# and some colors
#color_theme = c('#ffff99', '#8dd3c7', '#4daf4a', '#1f78b4') #yellow, blue, green, ?
#color_theme = c('#8dd3c7', '#4daf4a', '#cccccc') #blue, green, grey
color_theme = c('#cc3333', '#4daf4a', '#cccccc') #red, green, grey

i = 0
df_current_distr <- subset(df, distr_pair_id == i)

print(paste("rebalancing mechanism: ", df_current_distr$rebalancing_mechanism[1], sep=""))

# calculate average OSD load for highlighting
df_current_initial_distr <- subset(df_current_distr, rebalanced == "initial")
df_current_initial_distr_aggregated <- aggregate(df_current_initial_distr$osd_load, 
                                                 by=list(osd_id=df_current_initial_distr$osd_id), FUN=sum)
df_sum_shan <- Rmisc::summarySE(df_current_initial_distr_aggregated, "x")
average_load <- df_sum_shan$x[1]

rebalancing_mechanism = df_current_distr$rebalancing_mechanism[1]
if (startsWith(rebalancing_mechanism, "lpt_mean")) {
  rebalancing_factor = df_current_distr$lpt_factor[1] * 1048576
  print(paste("rebalncing factor:", rebalancing_factor))
  print(paste("average_load:", average_load))
}

output_pdf = paste(working_directory, "/pdfs/", "illustration_lpt_mean_1_1", ".pdf", sep = "")
pdf_title = df_current_distr$rebalancing_mechanism[1]
pdf(output_pdf, width=11, height=5, title=pdf_title)

tempplot=ggplot(data=df_current_distr,aes_string(x="rebalanced", y="osd_load", fill="moved")) + 
  #bar plot
  # add horizontal grey lines for average load and rebalancing factor ("Limit")
  geom_hline(yintercept = c(average_load, rebalancing_factor), color = "grey") +
  # hide the horizontal white grid lines that randomly appear
  theme(panel.grid.minor=element_blank()) +
  geom_bar(stat="identity", colour="black",)+
  facet_grid( ~ osd_id) +
  #facet_grid( ~ osd_id, labeller=labeller(osd_id = osd_lables)) +
  #hintergrund und so, wuerde ich so lassen
  #theme_classic()+
  #FARBEN einstellen, da findest du in nem anderen set evtl. grautoene
  scale_fill_manual(values=color_theme) + 
  #                       name="Data Placement",
  #                       breaks=c("random", "random_osd", "good"),
  #                       labels=c("Random File", "Random File Group", "LPT File Group")) +
  #hier wird die achsenbeschriftung gebastelt, ohne paste() koennte einfach ein "titel" angegeben werden
  labs(x = "", y = "") +
  #ticks an der y-achse
  #theme(axis.text.y = element_blank()) +
  #scale_y_continuous(breaks = c(average_load), labels = c("opt")) +
  scale_y_continuous(breaks = c(average_load, rebalancing_factor), labels = c("\nLower\nbound", "Limit")) +
  #scale_y_continuous() + 
  scale_x_discrete(limit = c("initial", "rebalanced"),
                   labels = c("random", "    new")) +
  theme(axis.text.x=element_text(angle = 90, vjust = 0.5)) +
  #remove legend
  theme(legend.position="none")+
  # define legend position
  #theme(legend.position= c(0.75, 0.25))+
  #remove title from legend
  #theme(legend.title=element_blank())+
  #change legend font size
  theme(legend.text = element_text(size=20), legend.title = element_text(size=20))+
  #ylim(-0.5,3)
  #schriftgroesse der beschriftungen
  theme(axis.title = element_text(size=20),axis.text=element_text(size=20))
plot(tempplot)
dev.off()
embedFonts(output_pdf)
tempplot

