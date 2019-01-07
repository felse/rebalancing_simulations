#working folder & packages#####
#set R Working Folder
input_file = "/home/felix/git/file_placement2/paper/figures/plots/osds_10_caps_100_bws_1_split_sizes_100_0.67_reps_1.csv"
output_file_name = "osds_10_caps_100_bws_1_split_sizes_100_0.67_reps_1_1000"

unit_conversion_factor = 1 #/ (1024 * 1024) #/(1000 * 60)

current_path <- getActiveDocumentContext()$path 
setwd(dirname(current_path ))

#use install.packages()
library(ggplot2)
library(reshape)
library(RColorBrewer) 
library(Rmisc)
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
color_theme = c('#cc3333', '#4daf4a', '#cccccc') #red, green, grey

i = 2
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
  rebalancing_factor = df_current_distr$lpt_factor[1] * 1048576# * average_load
  print(paste("rebalncing factor:", rebalancing_factor))
  print(paste("average_load:", average_load))
}

output_pdf = paste(working_directory, "/pdfs/", "illustration_lpt_mean_0_8", ".pdf", sep = "")
pdf_title = df_current_distr$rebalancing_mechanism[1]
pdf(output_pdf, width=11, height=5, title=pdf_title)

tempplot=ggplot(data=df_current_distr,aes_string(x="rebalanced", y="osd_load", fill="moved")) + 
  geom_hline(yintercept = c(average_load, rebalancing_factor), color = "grey") +
  theme(panel.grid.minor=element_blank()) +
  geom_bar(stat="identity", colour="black",)+
  facet_grid( ~ osd_id) +
  scale_fill_manual(values=color_theme) + 
  labs(x = "", y = "") +
  scale_y_continuous(breaks = c(average_load, rebalancing_factor), labels = c("\nLower\nbound", " \n\nLimit")) +
  scale_x_discrete(limit = c("initial", "rebalanced"),
                   labels = c("random", "    new")) +
  theme(axis.text.x=element_text(angle = 90, vjust = 0.5)) +
  theme(axis.text.y=element_text(vjust = .1)) +
  theme(legend.position="none")+
  theme(legend.text = element_text(size=20), legend.title = element_text(size=20))+
  theme(axis.title = element_text(size=20),axis.text=element_text(size=20))
plot(tempplot)
dev.off()
embedFonts(output_pdf)
tempplot

